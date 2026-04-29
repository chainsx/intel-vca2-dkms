#!/usr/bin/env python3
#
# Intel VCA Software Stack (VCASS)
#
# Python 3 compatible configuration merge helper.
#
# This file replaces the original Python 2 implementation shipped with
# Intel VCA 2.3.26.  The command-line interface and vcactl calls are kept
# compatible with the original script.
#

import abc
import copy
import os.path as fPath
import signal
import subprocess as proc
import sys
import xml.etree.ElementTree as XmlTree


UPDATE_ACTIONS = {
    "no_action": 0,      # option saved without change
    "apply_user": 1,     # option set to user value
    "wrn_apply_user": 2, # option set to user value, prints warning
    "new_default": 3,    # option set to new default value
    "delete": 4,         # option is deleted
    "error": 5,          # error
    "new_usr": 6,        # ask user to specify new value
    "unknown": 7,        # unhandled situation, triggers script exit
}


def decode_update_actions():
    return {value: key for key, value in UPDATE_ACTIONS.items()}


decoded_actions = {}


class BadXMLConfiguration(Exception):
    pass


class UnknownActionTaken(Exception):
    pass


class VcactlInvalidParameterName(Exception):
    def __init__(self):
        super().__init__("Invalid parameter passed to vcactl!")


class VcactlError(Exception):
    def __init__(self):
        super().__init__("vcactl error!")


class warning_holder:
    def __init__(self):
        self.__wrn_up = False

    def set_wrn_up(self):
        self.__wrn_up = True

    def check(self):
        return self.__wrn_up


WRN_UP = warning_holder()


class AbstractUpdate(metaclass=abc.ABCMeta):
    __option_state_dict = {
        "d": "in default state",
        "m": "modified by user",
        "del": "deleted",
        "nd": "in NEW default state",
    }

    def __init__(self):
        self.__print_debug = False
        self.__real_values = [None, None, None]

    def set_debug(self):
        print("[DEBUG] Debug mode is on, script will not run vcactl, script will only print command to run")
        self.__print_debug = True

    def _AbstractUpdate__decode_and_print_changes(self, changes):
        check_none = lambda val: str(val) if val is not None else "<not set>"
        print("\tOLD DEFAULT configuration: " + self.__option_state_dict[changes[0]] + "[" + check_none(self.__real_values[0]) + "]")
        print("\tUSER configuration:        " + self.__option_state_dict[changes[1]] + "[" + check_none(self.__real_values[1]) + "]")
        print("\tNEW DEFAULT configuration: " + self.__option_state_dict[changes[2]] + "[" + check_none(self.__real_values[2]) + "]")

    @abc.abstractmethod
    def _AbstractUpdate__decide_action(self, changes, option, cardId, nodeId, block_dev_name):
        return UPDATE_ACTIONS["unknown"]

    def __print_message(self, action, option, changes):
        if self.__print_debug:
            print("[DEBUG] " + decoded_actions.get(action, "unknown") + "[" + str(action) + "] on option: " + option + " changes vector: " + str(changes))

        if action == UPDATE_ACTIONS["unknown"]:
            raise UnknownActionTaken("[ERROR] Can not decide what update action take on option: " + option + " changes vector: " + str(changes))

        if action == UPDATE_ACTIONS["error"]:
            raise BadXMLConfiguration("[ERROR] USER configuration is corrupted. Missing option: " + option)

        if action == UPDATE_ACTIONS["wrn_apply_user"]:
            WRN_UP.set_wrn_up()
            check_none = lambda val: str(val) if val is not None else "<not set>"
            print("[WARNING] Option: " + option + " have new default value [" + check_none(self.__real_values[2]) + "]")

    def run(self, changes, option, real_values, cardId, nodeId, block_dev_name):
        self.__real_values = real_values
        action = self._AbstractUpdate__decide_action(changes, option, cardId, nodeId, block_dev_name)
        self.__print_message(action, option, changes)
        return action


def _ask_numeric_choice(prompt, default=2):
    try:
        answer = input(prompt)
        if answer == "":
            return default
        return int(answer)
    except (ValueError, EOFError, KeyboardInterrupt):
        return default


class ManualUpdate(AbstractUpdate):
    name = "Manual mode"

    def __ask_user(self, changes, option, cardId, nodeId, block_dev_name):
        if cardId is None and nodeId is None:
            option_info = "(global): "
        elif block_dev_name is not None:
            option_info = "for card " + str(cardId) + ", cpu " + str(nodeId) + ", " + block_dev_name + ": "
        else:
            option_info = "for card " + str(cardId) + ", cpu " + str(nodeId) + ": "

        print("Option " + option_info + option + " is in: ")
        super()._AbstractUpdate__decode_and_print_changes(changes)
        print("Please choose what to do from given options:")
        print("\t1. Apply USER value.")
        print("\t2. Use NEW default value.")
        print("\t3. Choose new value.")

        user_choice = _ask_numeric_choice("Action[2]:", 2)

        if user_choice == 1:
            return UPDATE_ACTIONS["apply_user"]
        if user_choice == 3:
            return UPDATE_ACTIONS["new_usr"]
        return UPDATE_ACTIONS["new_default"]

    def _AbstractUpdate__decide_action(self, changes, option, cardId, nodeId, block_dev_name):
        if changes[1] == "del" and (changes[0] == "d" and changes[2] == "d"):
            return UPDATE_ACTIONS["error"]
        return self.__ask_user(changes, option, cardId, nodeId, block_dev_name)


class SemiAutoUpdate(AbstractUpdate):
    name = "Semi-auto mode"

    def __ask_user(self, changes, option, cardId, nodeId, block_dev_name):
        if cardId is None and nodeId is None:
            option_info = "(global): "
        elif block_dev_name is not None:
            option_info = "for card " + str(cardId) + ", cpu " + str(nodeId) + ", " + block_dev_name + ": "
        else:
            option_info = "for card " + str(cardId) + ", cpu " + str(nodeId) + ": "

        print("Option " + option_info + option + " is in: ")
        super()._AbstractUpdate__decode_and_print_changes(changes)
        print("Please choose what to do from given options:")
        print("\t1. Apply USER value.")
        print("\t2. Use NEW default value.")
        print("\t3. Choose new value.")

        user_choice = _ask_numeric_choice("Action[2]:", 2)

        if user_choice == 1:
            return UPDATE_ACTIONS["apply_user"]
        if user_choice == 3:
            return UPDATE_ACTIONS["new_usr"]
        return UPDATE_ACTIONS["new_default"]

    def _AbstractUpdate__decide_action(self, changes, option, cardId, nodeId, block_dev_name):
        if changes[0] == "d":
            if changes[1] == "d":
                if changes[2] == "d":
                    return UPDATE_ACTIONS["no_action"]
                if changes[2] == "nd":
                    return UPDATE_ACTIONS["new_default"]
                if changes[2] == "del":
                    return UPDATE_ACTIONS["delete"]
            elif changes[1] == "m":
                if changes[2] == "d":
                    return UPDATE_ACTIONS["apply_user"]
                if changes[2] in ("nd", "del"):
                    return self.__ask_user(changes, option, cardId, nodeId, block_dev_name)
            elif changes[1] == "del":
                return UPDATE_ACTIONS["error"]

        if changes[0] == "del":
            if changes[1] == "m":
                if changes[2] == "del":
                    return UPDATE_ACTIONS["apply_user"]
                if changes[2] == "nd":
                    return UPDATE_ACTIONS["new_default"]
                return self.__ask_user(changes, option, cardId, nodeId, block_dev_name)

        return UPDATE_ACTIONS["unknown"]


class FullAutoUpdate(AbstractUpdate):
    name = "Full automatic mode"

    def _AbstractUpdate__decide_action(self, changes, option, cardId, nodeId, block_dev_name):
        if changes[0] == "d" and changes[1] == "m" and changes[2] == "d":
            return UPDATE_ACTIONS["apply_user"]
        if changes[0] in ("del", "d"):
            if changes[1] == "m":
                if changes[2] == "del":
                    return UPDATE_ACTIONS["apply_user"]
                if changes[2] in ("d", "nd"):
                    return UPDATE_ACTIONS["wrn_apply_user"]

        if changes[1] == "del" and (changes[0] == "d" and changes[2] == "d"):
            return UPDATE_ACTIONS["error"]

        if changes[2] == "del":
            return UPDATE_ACTIONS["delete"]

        if changes[0] == "d":
            if changes[1] == "d" and changes[2] in ("d", "nd"):
                return UPDATE_ACTIONS["no_action"] if changes[2] == "d" else UPDATE_ACTIONS["new_default"]

        return UPDATE_ACTIONS["unknown"]


class VcactlUpdater:
    def __init__(self, strategy, options, cardId=None, nodeId=None, block_dev_name=None):
        self.__cardId = cardId
        self.__nodeId = nodeId
        self.__block_dev_name = block_dev_name
        self.__strategy = strategy
        self.__options_in_xmls = options or {}
        self.__debug = False
        if cardId is not None and nodeId is not None:
            self.__vcactl_command_base = ["vcactl", "config", str(self.__cardId), str(self.__nodeId)]
            if block_dev_name is not None:
                self.__vcactl_command_base.append(block_dev_name)
        else:
            self.__vcactl_command_base = ["vcactl", "config"]

    def set_debug(self):
        self.__debug = True
        self.__strategy.set_debug()

    def __get_command(self, option, value):
        tmp = list(self.__vcactl_command_base)
        tmp.append(str(option))
        tmp.append("" if value is None else str(value))
        return tmp

    def __run_vcactl(self, option, value):
        if self.__debug:
            print(self.__get_command(option, value))
            return
        proc.check_call(self.__get_command(option, value))

    def __get_action(self, changes, option, values, cardId, nodeId, block_dev_name):
        return self.__strategy.run(changes, option, values, cardId, nodeId, block_dev_name)

    def __get_new_user_value(self, option_name):
        while True:
            try:
                return input("Please input new value for " + option_name + ": ")
            except EOFError:
                continue

    def __choose_value(self, action, option_entry, option_name):
        if action == UPDATE_ACTIONS["new_usr"]:
            return self.__get_new_user_value(option_name)
        if action == UPDATE_ACTIONS["no_action"]:
            return option_entry[0]
        if action in (UPDATE_ACTIONS["apply_user"], UPDATE_ACTIONS["wrn_apply_user"]):
            return option_entry[1]
        if action == UPDATE_ACTIONS["new_default"]:
            return option_entry[2]
        if action == UPDATE_ACTIONS["delete"]:
            return ""
        return None

    def __encode_changes(self, option_entry):
        if option_entry[0] == option_entry[1]:
            if option_entry[1] == option_entry[2]:
                return ["d", "d", "d"]
            if option_entry[2] is not None:
                return ["d", "d", "nd"]
            return ["d", "d", "del"]
        if option_entry[0] != option_entry[1] and option_entry[1] is not None:
            if option_entry[2] == option_entry[0]:
                return ["d", "m", "d"]
            if option_entry[2] is None:
                return ["d", "m", "del"]
            return ["d", "m", "nd"]
        if option_entry[0] is None and option_entry[1] is not None and option_entry[2] is None:
            return ["del", "m", "del"]
        if option_entry[0] == option_entry[2] and option_entry[1] is None:
            return ["d", "del", "d"]
        if option_entry[0] is None and option_entry[1] is not None and option_entry[2] is not None:
            return ["del", "m", "d"]
        if option_entry[0] is None and option_entry[1] is None and option_entry[2] is not None:
            return ["del", "del", "nd"]
        if option_entry[0] is None and option_entry[1] is None and option_entry[2] is None:
            return ["del", "del", "del"]
        return None

    def execute(self):
        for option_name, option_entry in self.__options_in_xmls.items():
            changes = self.__encode_changes(option_entry)
            action = self.__get_action(changes, option_name, option_entry,
                                       self.__cardId, self.__nodeId, self.__block_dev_name)
            value = self.__choose_value(action, option_entry, option_name)
            self.__run_vcactl(option_name, value)


class XMLContainer:
    def __init__(self, orginalDef, user, newDef):
        self.oldDef = XmlTree.parse(orginalDef)
        self.user = XmlTree.parse(user)
        self.newDef = XmlTree.parse(newDef)
        self.xml = {"o": self.oldDef, "u": self.user, "n": self.newDef}

    def __get_root_of(self, xmlConfigFile):
        return self.xml[xmlConfigFile].getroot()

    def __get_all_roots(self):
        return {xml: self.__get_root_of(xml) for xml in self.xml}

    def get_global_attribs(self):
        roots = self.__get_all_roots()
        global_attr = {}
        for config, root in roots.items():
            globalSection = root.findall("global")
            props = {}
            if globalSection:
                for item in globalSection[0]:
                    props[item.tag] = None if item.text == "None" else item.text
            global_attr[config] = props
        return global_attr

    def get_card_cpu_specific_attribs(self):
        roots = self.__get_all_roots()
        attr = {}
        for config, root in roots.items():
            all_card = [None] * 8
            for card in root.findall("card"):
                all_cpu = [None] * 3
                for cpu in card.findall("cpu"):
                    prop = {}
                    for item in cpu:
                        if item.tag == "block-devs":
                            continue
                        prop[item.tag] = item.text
                    all_cpu[int(cpu.attrib["id"])] = prop
                all_card[int(card.attrib["id"])] = copy.deepcopy(all_cpu)
            attr[config] = copy.deepcopy(all_card)
        return attr

    def get_block_devs_attribs(self):
        roots = self.__get_all_roots()
        mapped = {}
        for config, root in roots.items():
            block_devs = [[[] for _ in range(3)] for _ in range(8)]
            for card in root.findall("card"):
                for cpu in card.findall("cpu"):
                    bDevs = []
                    for block_dev in cpu.findall("block-devs"):
                        for dev in block_dev:
                            bDevs.append(dev)
                    block_devs[int(card.attrib["id"])][int(cpu.attrib["id"])] = bDevs
            mapped[config] = block_devs
        return mapped


XML_IDX = {"o": 0, "u": 1, "n": 2}


def _iter_safe(value):
    return value if value is not None else {}


def combine_properties(configurations, _type="global"):
    if _type == "global":
        result = {}
        for xml_configuration in configurations:
            for _property in configurations[xml_configuration]:
                result[_property] = [None] * 3

        for xml_configuration in configurations:
            for _property in configurations[xml_configuration]:
                result[_property][XML_IDX[xml_configuration]] = configurations[xml_configuration][_property]
        return result

    result = [[{} for _ in range(3)] for _ in range(8)]

    for xml_configuration in configurations:
        for card_id in range(len(configurations[xml_configuration])):
            if configurations[xml_configuration][card_id] is None:
                continue
            for cpu_id in range(len(configurations[xml_configuration][card_id])):
                cpu_entry = configurations[xml_configuration][card_id][cpu_id]
                if cpu_entry is None:
                    continue
                for item in cpu_entry:
                    if _type == "block_dev":
                        block_dev_name = item.tag
                        result[card_id][cpu_id][block_dev_name] = {}
                        for prop in item:
                            result[card_id][cpu_id][block_dev_name][prop.tag] = [None] * 3
                    else:
                        result[card_id][cpu_id][item] = [None] * 3

    for xml_configuration in configurations:
        for card_id in range(len(configurations[xml_configuration])):
            if configurations[xml_configuration][card_id] is None:
                continue
            for cpu_id in range(len(configurations[xml_configuration][card_id])):
                cpu_entry = configurations[xml_configuration][card_id][cpu_id]
                if cpu_entry is None:
                    continue
                for item in cpu_entry:
                    if _type == "block_dev":
                        block_dev_name = item.tag
                        for prop in item:
                            result[card_id][cpu_id][block_dev_name][prop.tag][XML_IDX[xml_configuration]] = prop.text
                    else:
                        result[card_id][cpu_id][item][XML_IDX[xml_configuration]] = cpu_entry[item]
    return result


def print_help():
    print("VCA configuration update script. Script performs update of VCA configuration. Can work in given modes:")
    print("\tmanual    - Always ask what to do.")
    print("\tsemi-auto - Will favour user set values, but in contested situations will ask user what to do.")
    print("\tfull-auto - Apply USER value when possible. May trigger ERROR(execution will be terminated) or show WARNING. This is default mode.")
    print("Example call:")
    print("\tvca_config_upgrade --mode manual")
    print("\tvca_config_upgrade -m full-auto")
    print('Calling with -h or --help will print this message.')
    sys.exit(0)


def arg_parse(argv):
    if len(argv) >= 2 and argv[1] == "help":
        print_help()
    if len(argv) < 4:
        raise RuntimeError('[ERROR] Bad arguments passed! First 3 arguments have to be the XML configuration files or 1st argument have to be: "help"')

    xml_files = []
    for i in range(1, 4):
        f_ext = fPath.splitext(argv[i])[1]
        if f_ext != ".xml":
            raise RuntimeError('[ERROR] Bad arguments passed! First 3 arguments have to be the XML configuration files or 1st argument have to be: "help"')
        xml_files.append(argv[i])

    other_opt = {}
    for i in range(4, len(argv)):
        if argv[i] == "debug":
            other_opt["dbg"] = 1
        elif argv[i] in ("manual", "full-auto", "semi-auto"):
            other_opt["up_mode"] = argv[i]
    return {"xml": xml_files, "other": other_opt}


UPDATE_MODE = {
    "full-auto": FullAutoUpdate,
    "semi-auto": SemiAutoUpdate,
    "manual": ManualUpdate,
}


def print_update_mode(update_mode):
    print("UPDATE MODE = " + update_mode.name)


def sigint_handler(_signal, _frame):
    print("\nCatched SIGINT! Aborting..")
    sys.exit(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)

    try:
        arg = arg_parse(sys.argv)
    except RuntimeError as err:
        print(str(err))
        print_help()

    try:
        xmlCont = XMLContainer(arg["xml"][0], arg["xml"][1], arg["xml"][2])
    except OSError as err:
        print("[ERROR] Cannot open file: " + str(getattr(err, "filename", "")))
        sys.exit(3)

    try:
        update_mode = UPDATE_MODE[arg["other"]["up_mode"]]()
    except KeyError:
        update_mode = UPDATE_MODE["full-auto"]()

    print_update_mode(update_mode)

    vca_updaters = []
    globalOptions = combine_properties(xmlCont.get_global_attribs())
    vca_updaters.append(VcactlUpdater(update_mode, globalOptions))

    cardCpuOpt = combine_properties(xmlCont.get_card_cpu_specific_attribs(), "cardCpu")
    block_dev_opt = combine_properties(xmlCont.get_block_devs_attribs(), "block_dev")

    for card in range(8):
        for cpu in range(3):
            vca_updaters.append(VcactlUpdater(update_mode, cardCpuOpt[card][cpu], card, cpu))
            for block_device in block_dev_opt[card][cpu]:
                vca_updaters.append(VcactlUpdater(update_mode, block_dev_opt[card][cpu][block_device],
                                                  card, cpu, block_dev_name=block_device))

    for update in vca_updaters:
        try:
            if arg["other"]["dbg"] == 1:
                decoded_actions = decode_update_actions()
                update.set_debug()
        except KeyError:
            pass
        try:
            update.execute()
        except (BadXMLConfiguration, UnknownActionTaken, proc.CalledProcessError) as err:
            print(str(err))
            if isinstance(err, BadXMLConfiguration):
                print("\tBad User XML configuration was passed. You probably intentionally deleted option by directly editing file with configuration.")
                print("\tOld configuration will be saved, but new default configuration will be used.")
                print("\tIf you want you can change it using 'vcactl' or by running this script in manual or semi-auto update mode:")
                print("\t\tvca_config_upgrade --mode manual")
                print("\t\tvca_config_upgrade --mode semi-auto")
                sys.exit(3)
            if isinstance(err, UnknownActionTaken):
                print("\tMerge run into conflict that can not be resolved in automatic mode because of unknown reasons.")
                print("\tOld configuration will be saved, but new default configuration will be used.")
                print("\tIf you want, you can change it using 'vcactl' or by running this script in manual or semi-auto update mode:")
                print("\t\tvca_config_upgrade --mode manual")
                print("\t\tvca_config_upgrade --mode semi-auto")
                sys.exit(3)
            if isinstance(err, proc.CalledProcessError):
                print("\tVcactl error occured. Aborting.")
                print("\tOld configuration will be saved, but new default configuration will be used.")
                print("\t\tvca_config_upgrade --mode manual")
                print("\t\tvca_config_upgrade --mode semi-auto")
                sys.exit(err.returncode)

    if WRN_UP.check():
        print("\tAutomatic merge ended correctly, but some contested situations occurred. Values set by USER where selected, but you should check")
        print("\tmessages labeled with [WARNING], and consider setting new value for this parameters.")
        print("\tYou can use 'vcactl' or run this script in manual or semi-auto update mode:")
        print("\t\tvca_config_upgrade --mode manual")
        print("\t\tvca_config_upgrade --mode semi-auto")

    print("Configuration update done!")
    sys.exit(0)
