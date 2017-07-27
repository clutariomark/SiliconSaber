# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SiliconSaber
                                 A QGIS plugin
 Plugin for Silicon-Saber
                             -------------------
        begin                : 2017-07-23
        copyright            : (C) 2017 by MVAC
        email                : mark.clutario@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load SiliconSaber class from file SiliconSaber.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .silicon_saber import SiliconSaber
    return SiliconSaber(iface)
