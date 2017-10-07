# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SiliconSaberDialog
                                 A QGIS plugin
 Plugin for Silicon-Saber
                             -------------------
        begin                : 2017-07-23
        git sha              : $Format:%H$
        copyright            : (C) 2017 by MVAC
        email                : mark.clutario@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt4 import QtGui, uic

FORM_CLASS1, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'silicon_saber_dialog_base.ui'))
    
FORM_CLASS2, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'silicon_saber_dialog_compute.ui'))
    
FORM_CLASS3, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'silicon_saber_dialog_create.ui'))
    
FORM_CLASS4, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'silicon_saber_dialog_import.ui'))
    
FORM_CLASS5, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'silicon_saber_dialog_commit.ui'))
    
FORM_CLASS6, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'silicon_saber_dialog_connect.ui'))

FORM_CLASS7, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'silicon_saber_dialog_run_sp.ui'))

class SiliconSaberDialogBase(QtGui.QDialog, FORM_CLASS1):
    def __init__(self, parent=None):
        """Constructor."""
        super(SiliconSaberDialogBase, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
class SiliconSaberDialogCompute(QtGui.QDialog, FORM_CLASS2):
    def __init__(self, parent=None):
        """Constructor."""
        super(SiliconSaberDialogCompute, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)\
        
class SiliconSaberDialogCreate(QtGui.QDialog, FORM_CLASS3):
    def __init__(self, parent=None):
        """Constructor."""
        super(SiliconSaberDialogCreate, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
class SiliconSaberDialogImport(QtGui.QDialog, FORM_CLASS4):
    def __init__(self, parent=None):
        """Constructor."""
        super(SiliconSaberDialogImport, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
class SiliconSaberDialogCommit(QtGui.QDialog, FORM_CLASS5):
    def __init__(self, parent=None):
        """Constructor."""
        super(SiliconSaberDialogCommit, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
class SiliconSaberDialogConnect(QtGui.QDialog, FORM_CLASS6):
    def __init__(self, parent=None):
        """Constructor."""
        super(SiliconSaberDialogConnect, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

class SiliconSaberDialogRunQuery(QtGui.QDialog, FORM_CLASS7):
    def __init__(self, parent=None):
        """Constructor."""
        super(SiliconSaberDialogRunQuery, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)