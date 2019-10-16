# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 by Simmo Saan <simmo.saan@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#
# History:
#
# 2019-10-15, Simmo Saan <simmo.saan@gmail.com> TODO
#   version 0.1: initial script
#

"""
Open buffers by full name
"""

from __future__ import print_function

SCRIPT_NAME = "buffer_open"
SCRIPT_AUTHOR = "Simmo Saan <simmo.saan@gmail.com>"
SCRIPT_VERSION = "0.1"
SCRIPT_LICENSE = "GPL3"
SCRIPT_DESC = "Open buffers by full name"

SCRIPT_REPO = "https://github.com/sim642/buffer_open"

SCRIPT_COMMAND = SCRIPT_NAME

IMPORT_OK = True

try:
    import weechat
except ImportError:
    print("This script must be run under WeeChat.")
    print("Get WeeChat now at: http://www.weechat.org/")
    IMPORT_OK = False

import re


SETTINGS = {
    "layout_apply": (
        "off",
        "open closed layout buffers on /layout apply"
    ),
    "max_closed": (
        "10",
        "maximum number of closed buffers to remember"
    )
}


def log(string):
    weechat.prnt("", "{}: {}".format(SCRIPT_NAME, string))


def error(string):
    weechat.prnt("", "{}{}: {}".format(weechat.prefix("error"), SCRIPT_NAME, string))


def command_plugin(plugin, command):
    weechat.command("", "/command {} {}".format(plugin, command))


def buffer_open_full_name_opened_cb(data, signal, hashtable):
    full_name = hashtable["full_name"]
    buffer = weechat.buffer_search("==", full_name)
    if buffer:
        # already open, do nothing
        return weechat.WEECHAT_RC_OK_EAT

    return weechat.WEECHAT_RC_OK


def buffer_open_full_name_unhandled_cb(data, signal, hashtable):
    full_name = hashtable["full_name"]
    error("no handler for opening buffer {}".format(full_name))
    return weechat.WEECHAT_RC_OK


TABLE = {
    # "full_name": ("plugin", "command"),
    "core.secured_data": ("core", "/secure"),
    "core.color": ("core", "/color"),
    "core.weechat": ("core", ""),  # do nothing because always open
    "fset.fset": ("fset", "/fset"),
    "irc.irc_raw": ("irc", "/server raw"),
    "relay.relay.list": ("relay", "/relay"),
    "relay.relay_raw": ("relay", "/relay raw"),
    "script.scripts": ("script", "/script"),
    "trigger.monitor": ("trigger", "/trigger monitor"),
    "xfer.xfer.list": ("xfer", "/xfer"),  # TODO: xfer DCC chat buffer
}


def buffer_open_full_name_table_cb(data, signal, hashtable):
    full_name = hashtable["full_name"]

    if full_name in TABLE:
        plugin, command = TABLE[full_name]
        command_plugin(plugin, command)
        return weechat.WEECHAT_RC_OK_EAT

    return weechat.WEECHAT_RC_OK


IRC_SERVER_RE = re.compile(r"irc\.server\.(.+)")
IRC_CHANNEL_RE = re.compile(r"irc\.([^.]+)\.(#.+)")  # TODO: other channel chars
IRC_QUERY_RE = re.compile(r"irc\.([^.]+)\.(.+)")


def buffer_open_full_name_irc_cb(data, signal, hashtable):
    full_name = hashtable["full_name"]
    noswitch = bool(int(hashtable.get("noswitch", "0")))

    noswitch_flag = "-noswitch " if noswitch else ""

    m = IRC_SERVER_RE.match(full_name)
    if m:
        server = m.group(1)
        command_plugin("irc", "/connect {}".format(server))  # /connect doesn't have -noswitch
        return weechat.WEECHAT_RC_OK_EAT

    m = IRC_CHANNEL_RE.match(full_name)
    if m:
        server = m.group(1)
        channel = m.group(2)
        command_plugin("irc", "/join {}-server {} {}".format(noswitch_flag, server, channel))
        return weechat.WEECHAT_RC_OK_EAT

    m = IRC_QUERY_RE.match(full_name)
    if m:
        server = m.group(1)
        nick = m.group(2)
        command_plugin("irc", "/query {}-server {} {}".format(noswitch_flag, server, nick))
        return weechat.WEECHAT_RC_OK_EAT

    return weechat.WEECHAT_RC_OK


def buffer_open_full_name(full_name, noswitch=None):
    hashtable = {
        "full_name": full_name
    }
    if noswitch is not None:
        hashtable["noswitch"] = str(int(noswitch))  # must be str for API

    weechat.hook_hsignal_send("buffer_open_full_name", hashtable)


def command_cb(data, buffer, args):
    args = args.split()
    if len(args) >= 1 and args[0] == "closed":
        if len(args) >= 2 and args[1] == "-list":
            if buffer_closed_stack:
                weechat.prnt("", "closed buffers (latest first):")
                for full_name in reversed(buffer_closed_stack):
                    weechat.prnt("", "  {}".format(full_name))
            else:
                weechat.prnt("", "no known closed buffers")
        else:
            if buffer_closed_stack:
                noswitch = len(args) >= 2 and args[1] == "-noswitch"
                full_name = buffer_closed_stack.pop()
                buffer_open_full_name(full_name, noswitch=noswitch)
            else:
                error("no known closed buffers")
                return weechat.WEECHAT_RC_ERROR
    elif len(args) >= 1:
        noswitch = args[0] == "-noswitch"
        if noswitch:
            if len(args) >= 2:
                full_name = args[1]
            else:
                error("missing full name")
                return weechat.WEECHAT_RC_ERROR
        else:
            full_name = args[0]
        buffer_open_full_name(full_name, noswitch=noswitch)
    else:
        error("unknown subcommand")
        return weechat.WEECHAT_RC_ERROR

    return weechat.WEECHAT_RC_OK


buffer_closed_stack = []


def buffer_closing_cb(data, signal, buffer):
    global buffer_closed_stack

    full_name = weechat.buffer_get_string(buffer, "full_name")
    buffer_closed_stack.append(full_name)

    max_closed = int(weechat.config_get_plugin("max_closed"))
    buffer_closed_stack = buffer_closed_stack[max(0, len(buffer_closed_stack) - max_closed):]
    return weechat.WEECHAT_RC_OK


LAYOUT_APPLY_RE = re.compile(r"/layout apply(?:\s+(\S+)(?:\s+buffers)?)?")


def layout_apply_cb(data, buffer, command):
    if weechat.config_string_to_boolean(weechat.config_get_plugin("layout_apply")):
        m = LAYOUT_APPLY_RE.match(command)
        if m:
            layout_name = m.group(1) or "default"
            hdata_layout = weechat.hdata_get("layout")
            layouts = weechat.hdata_get_list(hdata_layout, "gui_layouts")
            layout = weechat.hdata_search(hdata_layout, layouts, "${layout.name} == " + layout_name, 1)
            if layout:
                hdata_layout_buffer = weechat.hdata_get("layout_buffer")
                layout_buffer = weechat.hdata_pointer(hdata_layout, layout, "layout_buffers")
                while layout_buffer:
                    plugin_name = weechat.hdata_string(hdata_layout_buffer, layout_buffer, "plugin_name")
                    buffer_name = weechat.hdata_string(hdata_layout_buffer, layout_buffer, "buffer_name")
                    full_name = "{}.{}".format(plugin_name, buffer_name)

                    buffer = weechat.buffer_search("==", full_name)
                    if not buffer:
                        buffer_open_full_name(full_name, noswitch=True)

                    layout_buffer = weechat.hdata_move(hdata_layout_buffer, layout_buffer, 1)
    return weechat.WEECHAT_RC_OK


if __name__ == "__main__" and IMPORT_OK:
    if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "", ""):
        weechat.hook_hsignal("10000|buffer_open_full_name", "buffer_open_full_name_opened_cb", "")
        weechat.hook_hsignal("0|buffer_open_full_name", "buffer_open_full_name_unhandled_cb", "")

        weechat.hook_hsignal("500|buffer_open_full_name", "buffer_open_full_name_table_cb", "")
        weechat.hook_hsignal("500|buffer_open_full_name", "buffer_open_full_name_irc_cb", "")

        weechat.hook_command(SCRIPT_COMMAND, SCRIPT_DESC,
"""closed [-noswitch|-list]
  || [-noswitch] <full name>""",
"""""",
"""closed -noswitch|-list %-
  || -noswitch""".replace("\n", ""),
        "command_cb", "")

        weechat.hook_signal("buffer_closing", "buffer_closing_cb", "")
        weechat.hook_command_run("/layout apply*", "layout_apply_cb", "")

        for option, value in SETTINGS.items():
            if not weechat.config_is_set_plugin(option):
                weechat.config_set_plugin(option, value[0])

            weechat.config_set_desc_plugin(option, "{} (default: \"{}\")".format(value[1], value[0]))
