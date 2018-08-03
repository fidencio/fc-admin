#!./python-wrapper.sh
# -*- coding: utf-8 -*-
# vi:ts=2 sw=2 sts=2

# Copyright (C) 2015 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the licence, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# Authors: Alberto Ruiz <aruiz@redhat.com>
#          Oliver Gutiérrez <ogutierrez@redhat.com>

# Python imports
import sys
import os
import json
import logging
import inspect
import unittest

# GObject Introspection imports
import gi
from gi.repository import GLib
from gi.repository import Gio

PYTHONPATH = os.path.join(os.environ["TOPSRCDIR"], "logger")
sys.path.append(PYTHONPATH)

import fleet_commander_logger as FleetCommander

# Set logging level to debug
log = logging.getLogger()
level = logging.getLevelName("DEBUG")
log.setLevel(level)

# Get mainloop
ml = GLib.MainLoop()


# Test helpers

def mainloop_quit_callback(*args, **kwargs):
    logging.error(
        "Timed out waiting for file update notification. Test probably failed")
    ml.quit()


class MockConnectionManager(object):
    """
    Connection Manager mock class
    """
    def __init__(self):
        self.log = []

    def submit_change(self, namespace, data):
        logging.debug("Change submitted: %s - %s" % (namespace, data))
        self.log.append([namespace, data])

    def pop(self):
        return self.log.pop(0)


# Test data
PROFILES_FILE_CONTENT = """[General]
StartWithLastProfile=0

[Profile0]
Name=default
IsRelative=1
Path=robuvvg2.default
Default=1

[Profile1]
Name=Clean
IsRelative=1
Path=bd8ay27s.Clean
"""

PROFILES_FILE_CONTENT_NO_DEFAULT = """[General]
StartWithLastProfile=0

[Profile0]
Name=default
IsRelative=1
Path=robuvvg2.default

[Profile1]
Name=Clean
IsRelative=1
Path=bd8ay27s.Clean
"""

RAW_PREFS_DATA = r"""# Mozilla User Preferences

/* Do not edit this file.
 *
 * If you make changes to this file while the application is running,
 * the changes will be overwritten when the application exits.
 *
 * To make a manual change to preferences, you can visit the URL about:config
 */

user_pref("accessibility.typeaheadfind.flashBar", 0);
user_pref("beacon.enabled", false);
user_pref("browser.bookmarks.restore_default_bookmarks", false);
user_pref("browser.newtabpage.enhanced", false);
user_pref("browser.newtabpage.introShown", true);
user_pref("browser.newtabpage.storageVersion", 1);
user_pref("browser.uiCustomization.state", "{\"placements\":{\"widget-overflow-fixed-list\":[],\"PersonalToolbar\":[\"bookmarks-menu-button\",\"personal-bookmarks\"],\"nav-bar\":[\"back-button\",\"forward-button\",\"stop-reload-button\",\"home-button\",\"urlbar-container\",\"search-container\",\"downloads-button\",\"library-button\",\"abp-toolbarbutton\",\"qrcodeaddon-16\",\"action-button--jid0-9xfbwuwnvyx4wwsfbwmcm4jj69ejetpack-self-destructing-cookies\",\"ublock0-button\",\"VimFxButton\",\"ublock0_raymondhill_net-browser-action\",\"screenshots_mozilla_org-browser-action\",\"sidebar-button\",\"chrome-gnome-shell_gnome_org-browser-action\",\"preferences-button\",\"_4b6e6674-681a-45a4-98db-7c7d03df3560_-browser-action\"],\"TabsToolbar\":[\"tabbrowser-tabs\",\"new-tab-button\",\"alltabs-button\"],\"toolbar-menubar\":[\"menubar-items\"],\"addon-bar\":[\"addonbar-closebutton\",\"status-bar\"]},\"seen\":[\"abp-toolbarbutton\",\"loop-button\",\"pocket-button\",\"developer-button\",\"action-button--jid0-9xfbwuwnvpx4wwsfbwmcm4jj69ejetpack-self-destructing-cookies\",\"ublock0-button\",\"VimFxButton\",\"ublock0_raymondhill_net-browser-action\",\"webide-button\",\"screenshots_mozilla_org-browser-action\",\"chrome-gnome-shell_gnome_org-browser-action\",\"_4b6e6274-681a-45a4-98db-7c7d03df73560_-browser-action\"],\"dirtyAreaCache\":[\"PersonalToolbar\",\"nav-bar\",\"TabsToolbar\",\"toolbar-menubar\",\"PanelUI-contents\",\"addon-bar\"],\"currentVersion\":13,\"newElementCount\":3}");
user_pref("non\"standard,pref#name", 1);
"""

DEFAULT_PREFERENCES_DATA = {
    "accessibility.typeaheadfind.flashBar": 0,
    "beacon.enabled": False,
    "browser.bookmarks.restore_default_bookmarks": False,
    "browser.newtabpage.enhanced": False,
    "browser.newtabpage.introShown": True,
    "browser.newtabpage.storageVersion": 1,
    "browser.uiCustomization.state": "{\"placements\":{\"widget-overflow-fixed-list\":[],\"PersonalToolbar\":[\"bookmarks-menu-button\",\"personal-bookmarks\"],\"nav-bar\":[\"back-button\",\"forward-button\",\"stop-reload-button\",\"home-button\",\"urlbar-container\",\"search-container\",\"downloads-button\",\"library-button\",\"abp-toolbarbutton\",\"qrcodeaddon-16\",\"action-button--jid0-9xfbwuwnvyx4wwsfbwmcm4jj69ejetpack-self-destructing-cookies\",\"ublock0-button\",\"VimFxButton\",\"ublock0_raymondhill_net-browser-action\",\"screenshots_mozilla_org-browser-action\",\"sidebar-button\",\"chrome-gnome-shell_gnome_org-browser-action\",\"preferences-button\",\"_4b6e6674-681a-45a4-98db-7c7d03df3560_-browser-action\"],\"TabsToolbar\":[\"tabbrowser-tabs\",\"new-tab-button\",\"alltabs-button\"],\"toolbar-menubar\":[\"menubar-items\"],\"addon-bar\":[\"addonbar-closebutton\",\"status-bar\"]},\"seen\":[\"abp-toolbarbutton\",\"loop-button\",\"pocket-button\",\"developer-button\",\"action-button--jid0-9xfbwuwnvpx4wwsfbwmcm4jj69ejetpack-self-destructing-cookies\",\"ublock0-button\",\"VimFxButton\",\"ublock0_raymondhill_net-browser-action\",\"webide-button\",\"screenshots_mozilla_org-browser-action\",\"chrome-gnome-shell_gnome_org-browser-action\",\"_4b6e6274-681a-45a4-98db-7c7d03df73560_-browser-action\"],\"dirtyAreaCache\":[\"PersonalToolbar\",\"nav-bar\",\"TabsToolbar\",\"toolbar-menubar\",\"PanelUI-contents\",\"addon-bar\"],\"currentVersion\":13,\"newElementCount\":3}",
    "non\"standard,pref#name": 1
}

RAW_PREFS_DATA_MODIFIED = r"""# Mozilla User Preferences

/* Do not edit this file.
 *
 * If you make changes to this file while the application is running,
 * the changes will be overwritten when the application exits.
 *
 * To make a manual change to preferences, you can visit the URL about:config
 */

user_pref("accessibility.typeaheadfind.flashBar", 1);
user_pref("beacon.enabled", false);
user_pref("browser.bookmarks.restore_default_bookmarks", false);
user_pref("browser.newtabpage.enhanced", true);
user_pref("browser.newtabpage.testValue", 1);
user_pref("browser.uiCustomization.state", "{\"placements\":{\"widget-overflow-fixed-list\":[],\"PersonalToolbar\":[\"bookmarks-menu-button\",\"personal-bookmarks\"],\"nav-bar\":[\"back-button\",\"forward-button\",\"stop-reload-button\",\"home-button\",\"urlbar-container\",\"search-container\",\"downloads-button\",\"library-button\",\"abp-toolbarbutton\",\"qrcodeaddon-16\",\"action-button--jid0-9xfbwuwnvyx4wwsfbwmcm4jj69ejetpack-self-destructing-cookies\",\"ublock0-button\",\"VimFxButton\",\"ublock0_raymondhill_net-browser-action\",\"screenshots_mozilla_org-browser-action\",\"sidebar-button\",\"chrome-gnome-shell_gnome_org-browser-action\",\"preferences-button\",\"_4b6e6674-681a-45a4-98db-7c7d03df3560_-browser-action\"],\"TabsToolbar\":[\"tabbrowser-tabs\",\"new-tab-button\",\"alltabs-button\"],\"toolbar-menubar\":[\"menubar-items\"],\"addon-bar\":[\"addonbar-closebutton\",\"status-bar\"]},\"seen\":[\"abp-toolbarbutton\",\"loop-button\",\"pocket-button\",\"developer-button\",\"action-button--jid0-9xfbwuwnvpx4wwsfbwmcm4jj69ejetpack-self-destructing-cookies\",\"ublock0-button\",\"VimFxButton\",\"ublock0_raymondhill_net-browser-action\",\"webide-button\",\"screenshots_mozilla_org-browser-action\",\"chrome-gnome-shell_gnome_org-browser-action\",\"_4b6e6274-681a-45a4-98db-7c7d03df73560_-browser-action\"],\"dirtyAreaCache\":[\"PersonalToolbar\",\"nav-bar\",\"TabsToolbar\",\"toolbar-menubar\",\"PanelUI-contents\",\"addon-bar\"],\"currentVersion\":13,\"newElementCount\":3}");
"""

UPDATED_PREFERENCES_DATA = {
    "accessibility.typeaheadfind.flashBar": 1,
    "beacon.enabled": False,
    "browser.bookmarks.restore_default_bookmarks": False,
    "browser.newtabpage.enhanced": True,
    "browser.newtabpage.introShown": True,
    "browser.newtabpage.storageVersion": 1,
    "browser.uiCustomization.state": "{\"placements\":{\"widget-overflow-fixed-list\":[],\"PersonalToolbar\":[\"bookmarks-menu-button\",\"personal-bookmarks\"],\"nav-bar\":[\"back-button\",\"forward-button\",\"stop-reload-button\",\"home-button\",\"urlbar-container\",\"search-container\",\"downloads-button\",\"library-button\",\"abp-toolbarbutton\",\"qrcodeaddon-16\",\"action-button--jid0-9xfbwuwnvyx4wwsfbwmcm4jj69ejetpack-self-destructing-cookies\",\"ublock0-button\",\"VimFxButton\",\"ublock0_raymondhill_net-browser-action\",\"screenshots_mozilla_org-browser-action\",\"sidebar-button\",\"chrome-gnome-shell_gnome_org-browser-action\",\"preferences-button\",\"_4b6e6674-681a-45a4-98db-7c7d03df3560_-browser-action\"],\"TabsToolbar\":[\"tabbrowser-tabs\",\"new-tab-button\",\"alltabs-button\"],\"toolbar-menubar\":[\"menubar-items\"],\"addon-bar\":[\"addonbar-closebutton\",\"status-bar\"]},\"seen\":[\"abp-toolbarbutton\",\"loop-button\",\"pocket-button\",\"developer-button\",\"action-button--jid0-9xfbwuwnvpx4wwsfbwmcm4jj69ejetpack-self-destructing-cookies\",\"ublock0-button\",\"VimFxButton\",\"ublock0_raymondhill_net-browser-action\",\"webide-button\",\"screenshots_mozilla_org-browser-action\",\"chrome-gnome-shell_gnome_org-browser-action\",\"_4b6e6274-681a-45a4-98db-7c7d03df73560_-browser-action\"],\"dirtyAreaCache\":[\"PersonalToolbar\",\"nav-bar\",\"TabsToolbar\",\"toolbar-menubar\",\"PanelUI-contents\",\"addon-bar\"],\"currentVersion\":13,\"newElementCount\":3}",
    "non\"standard,pref#name": 1,
    "browser.newtabpage.testValue": 1
};


class TestFirefoxLogger(unittest.TestCase):

    maxDiff = None

    def setUp(self):
        pass

    def file_set_contents(self, filename, contents):
        with open(filename, 'w') as fd:
            fd.write(contents)
            fd.close()

    def setup_test_directory(self, profinit=True, prefsinit=True):
        # Create a temporary directory for testing
        TMPDIR = GLib.dir_make_tmp("fc_logger_firefox_XXXXXX")
        logging.debug("Testing data at dir %s" % TMPDIR)
        # Create profiles file
        if profinit:
            self.file_set_contents(
                os.path.join(TMPDIR, "profiles.ini"),
                PROFILES_FILE_CONTENT)
        # Create profile directory
        self.assertEqual(
            0,
            GLib.mkdir_with_parents(
                os.path.join(TMPDIR, "robuvvg2.default"),
                0o755))

        # Initialize preferences file
        if prefsinit:
            self.file_set_contents(
                os.path.join(TMPDIR, "robuvvg2.default", "prefs.js"),
                RAW_PREFS_DATA)

        return TMPDIR

    def test_01_default_profile_path(self):
        logging.info("Start test_01_default_profile_path")

        # Setup test directory
        TMPDIR = self.setup_test_directory(True, False)

        mgr = MockConnectionManager()
        firefox_logger = FleetCommander.FirefoxLogger(mgr, TMPDIR)

        # Get default profile
        self.assertEqual(
            os.path.join(TMPDIR, "robuvvg2.default"),
            firefox_logger.get_default_profile_path())

        # Try to get a default profile from a file without a default one
        self.file_set_contents(
            os.path.join(TMPDIR, "profiles.ini"),
            PROFILES_FILE_CONTENT_NO_DEFAULT)
        self.assertEqual(
            None,
            firefox_logger.get_default_profile_path())

        # Try to read a wrong profiles file
        self.file_set_contents(
            os.path.join(TMPDIR, "profiles.ini"),
            "RESISTANCE IS FUTILE")
        self.assertEqual(
            None,
            firefox_logger.get_default_profile_path())

        logging.info("End test_01_default_profile_path")


    def test_02_read_preferences(self):
        logging.info("Start test_02_read_preferences")

        # Setup test directory
        TMPDIR = self.setup_test_directory(True, False)
        mgr = MockConnectionManager()
        firefox_logger = FleetCommander.FirefoxLogger(mgr, TMPDIR)

        # Get preferences from given data
        returned = firefox_logger.load_firefox_preferences(RAW_PREFS_DATA)

        self.assertEqual(
            json.dumps(DEFAULT_PREFERENCES_DATA, sort_keys=True),
            json.dumps(returned, sort_keys=True))

        logging.info("End test_02_read_preferences")


    def test_03_profiles_file_load(self):
        logging.info("Start test_03_profiles_file_load")

        # Setup test directory with profile file
        TMPDIR = self.setup_test_directory(True, False)
        mgr = MockConnectionManager()
        firefox_logger = FleetCommander.FirefoxLogger(mgr, TMPDIR)
        # Profiles file is present. It should be initialized
        self.assertTrue(firefox_logger.default_profile_initialized)
        # Also there souldn't be any file monitor for it
        self.assertFalse(
            os.path.join(
                TMPDIR, "/profiles.ini") in firefox_logger.file_monitors)

        logging.info("End test_03_profiles_file_load")

    def test_04_profiles_file_load_wrong(self):
        logging.info("Start test_04_profiles_file_load_wrong")

        # Setup test directory without profile file
        TMPDIR = self.setup_test_directory(False, False)
        # Add profiles file without default profile
        self.file_set_contents(
            os.path.join(TMPDIR, "profiles.ini"),
            PROFILES_FILE_CONTENT_NO_DEFAULT)
        mgr = MockConnectionManager()
        firefox_logger = FleetCommander.FirefoxLogger(mgr, TMPDIR)
        # Profiles file is present but wrong. It shouldn't be initialized
        self.assertFalse(firefox_logger.default_profile_initialized)
        # Also there souldn't be a file monitor for it
        self.assertTrue(
            os.path.join(
                TMPDIR, "profiles.ini") in firefox_logger.file_monitors)

        logging.info("End test_04_profiles_file_load_wrong")

    def test_05_profiles_file_monitoring_no_default(self):
        logging.info("Start test_05_profiles_file_monitoring_no_default")

        # Setup test directory
        TMPDIR = self.setup_test_directory(False, False)

        mgr = MockConnectionManager()
        firefox_logger = FleetCommander.FirefoxLogger(mgr, TMPDIR)

        # Profiles file is not present. It should not be initialized
        self.assertFalse(firefox_logger.default_profile_initialized)

        # Setup callback for profiles file update
        firefox_logger.test_profiles_file_updated = ml.quit

        # Setup a timeout for this test to quit and fail if timeout is reached
        timeout = GLib.timeout_add(
            1000,
            mainloop_quit_callback)

        # Add profiles file without default profile
        self.file_set_contents(
            os.path.join(TMPDIR, "profiles.ini"),
            PROFILES_FILE_CONTENT_NO_DEFAULT)

        # Execute main loop
        ml.run()

        # Default profile should not be initialized yet
        self.assertFalse(firefox_logger.default_profile_initialized)

        logging.info("End test_05_profiles_file_monitoring_no_default")


    def test_06_profiles_file_monitoring(self):
        logging.info("Start test_06_profiles_file_monitoring")

        # Setup test directory
        TMPDIR = self.setup_test_directory(False, False)

        mgr = MockConnectionManager()
        firefox_logger = FleetCommander.FirefoxLogger(mgr, TMPDIR)

        # Profiles file is not present. It should not be initialized
        self.assertFalse(firefox_logger.default_profile_initialized)

        # File monitor should be set and waiting for changes
        self.assertTrue(
            os.path.join(
                TMPDIR, "profiles.ini") in firefox_logger.file_monitors)

        # Setup callback for profiles file update
        firefox_logger.test_profiles_file_updated = ml.quit

        # Setup a timeout for this test to quit and fail if timeout is reached
        timeout = GLib.timeout_add(
            1000,
            mainloop_quit_callback)

        # Add profiles file
        self.file_set_contents(
            os.path.join(TMPDIR, "profiles.ini"),
            PROFILES_FILE_CONTENT)

        # Execute main loop
        ml.run()
        # Default profile preferences should be initialized at this point
        self.assertTrue(firefox_logger.default_profile_initialized)

        logging.info("End test_06_profiles_file_monitoring")


    def test_07_preferences_file_monitoring_wrong(self):
        logging.info("Start test_07_preferences_file_monitoring_wrong")

        # Setup test directory
        TMPDIR = self.setup_test_directory(True, False)

        mgr = MockConnectionManager()
        firefox_logger = FleetCommander.FirefoxLogger(mgr, TMPDIR)
        prefs_path = os.path.join(TMPDIR, "robuvvg2.default/prefs.js")
        # Profiles file is present. It should be initialized
        self.assertTrue(firefox_logger.default_profile_initialized)

        # Default profile preferences file is not present. Shouldn't be initialized
        self.assertFalse(firefox_logger.default_profile_prefs_initialized)

        # Current preferences should be empty
        self.assertEqual(
            json.dumps({}),
            json.dumps(firefox_logger.monitored_preferences))

        # Setup callback on profiles file update
        firefox_logger.test_prefs_file_updated = ml.quit

        # Setup a timeout for this test to quit and fail if timeout is reached
        timeout = GLib.timeout_add(
            1000,
            mainloop_quit_callback)

        # Add profiles file
        self.file_set_contents(
            prefs_path,
            "WRONG CONTENT")

        # Execute main loop
        ml.run()

        # Default profile preferences should be initialized as empty due to
        # wrong contents
        self.assertTrue(firefox_logger.default_profile_prefs_initialized)

        # Wrong content only leads to empty preferences
        self.assertEqual(
            json.dumps({prefs_path: {}}),
            json.dumps(firefox_logger.monitored_preferences))

        logging.info("End test_07_preferences_file_monitoring_wrong")


    def test_08_preferences_file_monitoring(self):
        logging.info("Start test_08_preferences_file_monitoring")

        # Setup test directory
        TMPDIR = self.setup_test_directory(True, False)

        mgr = MockConnectionManager()
        firefox_logger = FleetCommander.FirefoxLogger(mgr, TMPDIR)
        prefs_path = os.path.join(TMPDIR, "robuvvg2.default/prefs.js")

        # Profiles file is present. It should be initialized
        self.assertTrue(firefox_logger.default_profile_initialized)

        # Preferences file is not present. It shouldn't be initialized
        self.assertFalse(firefox_logger.default_profile_prefs_initialized)

        # Preferences data should be empty
        self.assertEqual(
            json.dumps({}),
            json.dumps(firefox_logger.monitored_preferences))

        # Setup callback on profiles file update
        firefox_logger.test_prefs_file_updated = ml.quit

        # Setup a timeout for this test to quit and fail if timeout is reached
        timeout = GLib.timeout_add(
            1000,
            mainloop_quit_callback)

        # Add profiles file
        self.file_set_contents(
            prefs_path,
            RAW_PREFS_DATA)

        # Execute main loop
        ml.run()

        # Preferences file is now present. It should be initialized
        self.assertTrue(firefox_logger.default_profile_prefs_initialized)

        # Default preference data should be loaded
        self.assertEqual(
            json.dumps({prefs_path: DEFAULT_PREFERENCES_DATA}, sort_keys=True),
            json.dumps(firefox_logger.monitored_preferences, sort_keys=True))

        logging.info("End test_08_preferences_file_monitoring")


    def test_09_preferences_file_loading(self):
        logging.info("Start test_09_preferences_file_loading")

        # Setup test directory
        TMPDIR = self.setup_test_directory(True, True)

        mgr = MockConnectionManager()
        firefox_logger = FleetCommander.FirefoxLogger(mgr, TMPDIR)
        prefs_path = os.path.join(TMPDIR, "robuvvg2.default/prefs.js")

        # Profiles file is present. It should be initialized
        self.assertTrue(firefox_logger.default_profile_initialized)

        # Preferences file is now present. It should be initialized
        self.assertTrue(firefox_logger.default_profile_prefs_initialized)

        # Default preference data should be loaded
        self.assertEqual(
            json.dumps({prefs_path: DEFAULT_PREFERENCES_DATA}, sort_keys=True),
            json.dumps(firefox_logger.monitored_preferences, sort_keys=True))

        logging.info("End test_09_preferences_file_loading")


    def test_10_preferences_update(self):
        logging.info("Start test_10_preferences_update")

        # Setup test directory
        TMPDIR = self.setup_test_directory(True, True)

        mgr = MockConnectionManager()
        firefox_logger = FleetCommander.FirefoxLogger(mgr, TMPDIR)
        prefs_path = os.path.join(TMPDIR, "robuvvg2.default/prefs.js")

        # Profiles file is present. It should be initialized
        self.assertTrue(firefox_logger.default_profile_initialized)

        # Preferences file is now present. It should be initialized
        self.assertTrue(firefox_logger.default_profile_prefs_initialized)

        # Default preference data should be loaded
        self.assertEqual(
            json.dumps({prefs_path: DEFAULT_PREFERENCES_DATA}, sort_keys=True),
            json.dumps(firefox_logger.monitored_preferences, sort_keys=True))

        # Setup callback on profiles file update
        firefox_logger.test_prefs_file_updated = ml.quit

        # Setup a timeout for this test to quit and fail if timeout is reached
        timeout = GLib.timeout_add(
            1000,
            mainloop_quit_callback)

        # Overwrite profiles file with modified data
        self.file_set_contents(
            prefs_path,
            RAW_PREFS_DATA_MODIFIED)

        # Execute main loop
        ml.run()

        # Check preference data has been updated
        self.assertEqual(
            json.dumps({prefs_path: UPDATED_PREFERENCES_DATA}, sort_keys=True),
            json.dumps(firefox_logger.monitored_preferences, sort_keys=True))

        # Changes queue length should be 3
        self.assertEqual(3, len(mgr.log))

        # Config changes should be submitted
        settings = [
            json.dumps(
                [
                    "org.mozilla.firefox",
                    json.dumps(
                        {
                            "key": "accessibility.typeaheadfind.flashBar",
                            "value": 1
                        }, sort_keys=True)
                ]),
            json.dumps(
                [
                    "org.mozilla.firefox",
                    json.dumps(
                        {
                            "key": "browser.newtabpage.enhanced",
                            "value": True
                        }, sort_keys=True)
                ]),
            json.dumps(
                [
                    "org.mozilla.firefox",
                    json.dumps(
                        {
                            "key": "browser.newtabpage.testValue",
                            "value": 1
                        }, sort_keys=True)
                ]),
        ]

        while len(mgr.log) > 0:
            setting = mgr.log.pop(0)
            jsonsetting = json.dumps(setting)
            self.assertTrue(jsonsetting in settings)

        # Changes queue length should be 0
        self.assertEqual(0, len(mgr.log))

        logging.info("End test_10_preferences_update")


if __name__ == "__main__":
    unittest.main()
