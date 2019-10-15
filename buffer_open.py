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


IRC_SERVER_RE = re.compile(r"irc\.server\.(.+)")
IRC_CHANNEL_RE = re.compile(r"irc\.([^.]+)\.(#.+)")  # TODO: other channel chars
IRC_QUERY_RE = re.compile(r"irc\.([^.]+)\.(.+)")


def buffer_open_full_name_irc_cb(data, signal, hashtable):
    full_name = hashtable["full_name"]
    noswitch = bool(hashtable.get("noswitch", 0))  # TODO: actually use

    m = IRC_SERVER_RE.match(full_name)
    if m:
        server = m.group(1)
        command_plugin("irc", "/connect {}".format(server))
        return weechat.WEECHAT_RC_OK_EAT

    m = IRC_CHANNEL_RE.match(full_name)
    if m:
        server = m.group(1)
        channel = m.group(2)
        command_plugin("irc", "/join -server {} {}".format(server, channel))
        return weechat.WEECHAT_RC_OK_EAT

    m = IRC_QUERY_RE.match(full_name)
    if m:
        server = m.group(1)
        nick = m.group(2)
        command_plugin("irc", "/query -server {} {}".format(server, nick))
        return weechat.WEECHAT_RC_OK_EAT

    return weechat.WEECHAT_RC_OK


def buffer_open_full_name(full_name):
    weechat.hook_hsignal_send("buffer_open_full_name", {
        "full_name": full_name
    })


def command_cb(data, buffer, args):
    if args == "closed":
        if buffer_closed_stack:
            full_name = buffer_closed_stack.pop()
            buffer_open_full_name(full_name)
        else:
            error("no known closed buffers")
    else:
        buffer_open_full_name(args)

    return weechat.WEECHAT_RC_OK


buffer_closed_stack = []


def buffer_closing_cb(data, signal, buffer):
    full_name = weechat.buffer_get_string(buffer, "full_name")
    buffer_closed_stack.append(full_name)  # TODO: add limit for stack size
    return weechat.WEECHAT_RC_OK


if __name__ == "__main__" and IMPORT_OK:
    if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "", ""):
        weechat.hook_hsignal("10000|buffer_open_full_name", "buffer_open_full_name_opened_cb", "")
        weechat.hook_hsignal("0|buffer_open_full_name", "buffer_open_full_name_unhandled_cb", "")

        weechat.hook_hsignal("500|buffer_open_full_name", "buffer_open_full_name_irc_cb", "")

        weechat.hook_command(SCRIPT_COMMAND, SCRIPT_DESC,
"""""",
"""""",
"""""".replace("\n", ""),
        "command_cb", "")

        weechat.hook_signal("buffer_closing", "buffer_closing_cb", "")

        for option, value in SETTINGS.items():
            if not weechat.config_is_set_plugin(option):
                weechat.config_set_plugin(option, value[0])

            weechat.config_set_desc_plugin(option, "{} (default: \"{}\")".format(value[1], value[0]))
