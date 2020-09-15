init -990 python in mas_submod_utils:
    ei_submod = Submod(
        author="multimokia",
        name="Enhanced Idle",
        description=(
            "This submod adds a slight adjustment to the idle sprites for those who are affectionate or above with Monika. "
            "Allowing her to occasionally look over at what you're doing."
        ),
        version="1.1.0"
    )

init -989 python in ei_utils:
    import store

    #Register the updater if needed
    if store.mas_submod_utils.isSubmodInstalled("Submod Updater Plugin"):
        store.sup_utils.SubmodUpdater(
            submod=store.mas_submod_utils.ei_submod,
            user_name="multimokia",
            repository_name="MAS-Submod-Enhanced-Idle",
            tag_formatter=lambda x: x[x.index('_') + 1:],
            update_dir="",
            attachment_id=None,
        )

init 999 python in ei_utils:
    import subprocess

    DEF_MOUSE_POS_RETURN = (0, 0)

    def proc_output_to_dict(raw_return):
        """
        Converts raw_return to dict format for better handling

        IN:
            raw_return - the return of the subprocess.check_output call

        OUT:
            dict() - formatted version of the output
        """
        return_list = raw_return.split('\n')

        formatted_return = dict()
        for info in return_list:
            equal_index = info.find('=')

            #We do some light preprocessing here to make sure we actually have something valid
            #NOTE: This does assume there's something after the equals sign
            if equal_index > 0:
                formatted_return[info[:equal_index]] = info[equal_index + 1:]

        return formatted_return

    def safe_check_output(command):
        """
        Wrapper for subprocess.check_output which logs errors and returns None if failed

        IN:
            command - The command to run (plus follow up arguments) in list format (same as subprocess.check_output)

        OUT:
            The results of the command if success, or None if failure
        """
        try:
            return subprocess.check_output(command)
        except Exception as e:
            store.mas_utils.writelog("[ERROR]: Failed to check output for command struct: {0}. Error: {1}\n".format(
                command, e
            ))
            #Return None to indicate failure
            return None

    def getMousePosWin():
        """
        Returns an (x, y) co-ord tuple for the mouse position

        OUT:
            tuple representing the position of the mouse
        """
        if store.mas_windowreacts.can_do_windowreacts:
            #Try except here because we may not have permissions to do so
            try:
                cur_pos = store.win32gui.GetCursorPos()
            except:
                cur_pos = DEF_MOUSE_POS_RETURN

        else:
            cur_pos = DEF_MOUSE_POS_RETURN

        return cur_pos

    def getMousePosLin():
        """
        Returns an (x, y) co-ord tuple for the mouse position

        OUT:
            tuple representing mouse position
        """
        if store.mas_windowreacts.can_do_windowreacts:
            raw_pos = safe_check_output(["xdotool", "getmouselocation", "--shell"])

            #Make sure we don't try to process bad coords
            if raw_pos is None:
                return DEF_MOUSE_POS_RETURN

            #Convert to dict for easy gets
            pos_data = proc_output_to_dict(raw_pos)

            return (
                store.mas_utils.tryparseint(pos_data.get("X", 0), 0),
                store.mas_utils.tryparseint(pos_data.get("Y", 0), 0)
            )

        else:
            return DEF_MOUSE_POS_RETURN

    def getMASWindowHWND():
        """
        Gets the hWnd of the MAS window

        NOTE: Windows ONLY

        OUT:
            int - represents the hWnd of the MAS window
        """
        def checkMASWindow(hwnd, lParam):
            """
            Internal function to identify the MAS window. Raises an exception when found to allow the main func to return
            """
            if renpy.config.window_title in store.win32gui.GetWindowText(hwnd):
                raise Exception(hwnd)

        try:
            store.win32gui.EnumWindows(checkMASWindow, None)
        except Exception as e:
            return e.message

    def getMASWindowID():
        """
        Gets the window id of the MAS window

        NOTE: Linux ONLY (unless Mac supports xdotool too)

        OUT:
            int - represents the window id of the MAS window
        """
        raw_out = safe_check_output(["xdotool", "search", "--name", "^{0}$".format(renpy.config.window_title)])

        #Make sure we don't attempt to .strip('\n') a NoneType
        if raw_out is None:
            return 0

        return store.mas_utils.tryparseint(
            raw_out.strip('\n'),
            0
        )

    def getMASWindowPosWin():
        """
        Gets the window position for MAS as a tuple of (left, top, right, bottom)

        OUT:
            tuple representing window geometry or None if the window's hWnd could not be found
        """
        hwnd = getMASWindowHWND()

        if hwnd is None:
            return None

        return store.win32gui.GetWindowRect(hwnd)

    def getMASWindowPosLin():
        """
        Gets the window position for MAS as a tuple of (left, top, right, bottom)

        OUT:
            tuple representing window geometry or None if the window id cannot be found
        """
        win_id = getMASWindowID()

        if win_id == 0:
            return None

        #Get the data and convert to a more useable
        raw_geo = safe_check_output(["xdotool", "getwindowgeometry", "--shell", "{0}".format(win_id)])

        #If we couldn't get the geometry, then we just return None
        if raw_geo is None:
            return None

        geo_data = proc_output_to_dict(raw_geo)

        #Fetch left and top for use to calculate right and bottom
        left = store.mas_utils.tryparseint(geo_data.get("X", 0), 0)
        top = store.mas_utils.tryparseint(geo_data.get("Y", 0), 0)

        #Now we need to math for right and bottom
        right = left + store.mas_utils.tryparseint(geo_data.get("WIDTH", 0), 0)
        bottom = top + store.mas_utils.tryparseint(geo_data.get("HEIGHT", 0), 0)

        return (left, top, right, bottom)

    def isCursorInMASWindow():
        """
        Checks if the cursor is within the MAS window

        OUT:
            True if cursor is within the mas window (within x/y), False otherwise
            Also returns True if we cannot get window position
        """
        pos_tuple = getMASWindowPos()

        if pos_tuple is None:
            return True

        left, top, right, bottom = pos_tuple

        cur_x, cur_y = getMousePos()

        if not (left <= cur_x <= right):
            return False

        if not (top <= cur_y <= bottom):
            return False

        return True


    def isCursorLeftOfMASWindow():
        """
        Checks if the cursor is to the left of the MAS window (must be explicitly to the left of the left window bound)

        OUT:
            True if cursor is to the left of the window, False otherwise
            Also returns False if we cannot get window position
        """
        pos_tuple = getMASWindowPos()

        if pos_tuple is None:
            return False

        left, top, right, bottom = pos_tuple

        cur_x, cur_y = getMousePos()

        if cur_x < left:
            return True
        return False

    def isCursorRightOfMASWindow():
        """
        Checks if the cursor is to the right of the MAS window (must be explicitly to the right of the right window bound)

        OUT:
            True if cursor is to the right of the window, False otherwise
            Also returns False if we cannot get window position
        """
        pos_tuple = getMASWindowPos()

        if pos_tuple is None:
            return False

        left, top, right, bottom = pos_tuple

        cur_x, cur_y = getMousePos()

        if cur_x > right:
            return True
        return False

    def ret_false():
        """
        Literally just returns False
        """
        return False

    def ret_true():
        """
        Literally just returns True
        """
        return True

    #Now with everything defined, let's setup our core functions
    if renpy.windows:
        getMASWindowPos = getMASWindowPosWin
        getMousePos = getMousePosWin

    elif renpy.linux:
        getMASWindowPos = getMASWindowPosLin
        getMousePos = getMousePosLin

    #No Mac support as cannot test. We'll just keep this here to maintain the standard behaviour of idle
    else:
        isCursorInMASWindow = ret_true
        isCursorLeftOfMASWindow = ret_false
        isCursorRightOfMASWindow = ret_false

#Shorthand for follow sprites as they're used in multiple idle anims
image monika 1eua_follow = ConditionSwitch(
    "ei_utils.isCursorRightOfMASWindow()","monika 1lua",
    "ei_utils.isCursorLeftOfMASWindow()", "monika 1rua",
    "True", "monika 1eua"
)

image monika 5esu_follow = ConditionSwitch(
    "ei_utils.isCursorRightOfMASWindow()","monika 5lsu",
    "ei_utils.isCursorLeftOfMASWindow()", "monika 5rsu",
    "True", "monika 5esu"
)

image monika 5eubla_follow = ConditionSwitch(
    "ei_utils.isCursorRightOfMASWindow()","monika 5lubla",
    "ei_utils.isCursorLeftOfMASWindow()", "monika 5rublu",
    "True", "monika 5eubla"
)

image monika 5eubsa_follow = ConditionSwitch(
    "ei_utils.isCursorRightOfMASWindow()","monika 5lubsa",
    "ei_utils.isCursorLeftOfMASWindow()", "monika 5rubsu",
    "True", "monika 5eubsa"
)

#Overrides for idle ATL parts
init 1:
    #AFFECTIONATE
    image monika ATL_affectionate:
        block:
            choice 0.7:
                #Select image
                block:
                    choice 0.02:
                        "monika 1eua"
                        1.0
                        choice:
                            "monika 1sua"
                            4.0
                        choice:
                            "monika 1kua"
                            1.5

                        "monika 1eua"

                    choice 0.98:
                        choice 0.94898:
                            "monika 1eua"
                        choice 0.051020:
                            "monika 1hua"

            choice 0.3:
                #Select image
                block:
                    choice 0.02:
                        "monika 1eua_follow"
                        1.0
                        choice:
                            "monika 1sua"
                            4.0
                        choice:
                            "monika 1kua"
                            1.5

                        "monika 1eua_follow"

                    choice 0.98:
                        choice 0.94898:
                            "monika 1eua_follow"
                        choice 0.051020:
                            "monika 1hua"

            # select wait time
            block:
                choice:
                    20.0
                choice:
                    22.0
                choice:
                    24.0
                choice:
                    26.0
                choice:
                    28.0
                choice:
                    30.0

            repeat

    #ENAMORED
    image monika ATL_enamored:
        # 1 time this part
        "monika 1eua"
        5.0

        # repeat
        block:
            choice:
                # select image
                block:
                    choice 0.02:
                        "monika 1eua"
                        1.0
                        choice:
                            "monika 1sua"
                            4.0
                        choice:
                            "monika 1kua"
                            1.5
                        "monika 1eua"

                    choice 0.98:
                        choice 0.765306:
                            "monika 1eua"
                        choice 0.112245:
                            "monika 5esu"
                        choice 0.061224:
                            "monika 5tsu"
                        choice 0.061224:
                            "monika 1huu"

            choice:
                # select image
                block:
                    choice 0.02:
                        "monika 1eua_follow"
                        1.0
                        choice:
                            "monika 1sua"
                            4.0
                        choice:
                            "monika 1kua"
                            1.5

                        "monika 1eua_follow"

                    choice 0.98:
                        choice 0.765306:
                            "monika 1eua_follow"
                        choice 0.112245:
                            "monika 5esu_follow"
                        choice 0.061224:
                            "monika 5tsu"
                        choice 0.061224:
                            "monika 1huu"

            # select wait time
            block:
                choice:
                    20.0
                choice:
                    22.0
                choice:
                    24.0
                choice:
                    26.0
                choice:
                    28.0
                choice:
                    30.0

            repeat

    #LOVE
    image monika ATL_love:
        # 1 time this parrt
        "monika 1eua"
        5.0

        # repeat
        block:
            choice 0.3:
                # select image
                block:
                    choice 0.02:
                        "monika 1eua"
                        1.0
                        choice:
                            "monika 1sua"
                            4.0
                        choice:
                            "monika 1kua"
                            1.5
                        "monika 1eua"

                    choice 0.98:
                        choice 0.510104:
                            "monika 1eua"
                        choice 0.255102:
                            "monika 5esu"
                        choice 0.091837:
                            "monika 5tsu"
                        choice 0.091837:
                            "monika 1huu"
                        choice 0.051020:
                            "monika 5eubla"

            choice 0.7:
                block:
                    choice 0.02:
                        "monika 1eua_follow"
                        1.0

                        choice:
                            "monika 1sua"
                            4.0
                        choice:
                            "monika 1kua"
                            1.5
                        choice:
                            "monika 5eubsa_follow"
                            20

                        "monika 1eua_follow"

                    choice 0.98:
                        choice 0.510104:
                            "monika 1eua_follow"

                        choice 0.255102:
                            "monika 5esu_follow"

                        choice 0.091837:
                            "monika 5tsu"

                        choice 0.091837:
                            "monika 1huu"

                        choice 0.051020:
                            "monika 5eubla_follow"

            # select wait time
            block:
                choice:
                    20.0
                choice:
                    22.0
                choice:
                    24.0
                choice:
                    26.0
                choice:
                    28.0
                choice:
                    30.0

            repeat
