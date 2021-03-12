import xbmc
import xbmcaddon
import sys

addon = xbmcaddon.Addon()
name = addon.getAddonInfo('name')


def log(msg, level=xbmc.LOGINFO):
    # override message level to force logging when addon logging turned on
    if addon.getSetting('addon_debug') == 'true' and level == xbmc.LOGDEBUG:
        if sys.version_info[0] == 3:
            level = xbmc.LOGINFO
        else:
            level = xbmc.LOGNOTICE
    
    try:

        xbmc.log('%s: %s' % (name, msg), level)
    except Exception as e:
        try: xbmc.log('Logging Failure: %s' % (e), level)
        except: pass  # just give up
