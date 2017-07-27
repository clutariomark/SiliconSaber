# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SiliconSaber
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant
from PyQt4.QtGui import QAction, QIcon

from qgis.core import *
import subprocess
import os
import pyodbc

# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from silicon_saber_dialog import *
import processing


class SiliconSaber:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SiliconSaber_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SiliconSaber')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'SiliconSaber')
        self.toolbar.setObjectName(u'SiliconSaber')
        self.count = 0
        
        self.column_names = ["id", "mapId", "layer", "level", "active", "vertices", "elev",
            "centerGvt", "ombb", "orient", "desc", "access", "color", "trnp", "outline", "scaling", 
            "name", "number", "geoId", "roleId", "funcId", "area", "length", "centroid"]
            
        self.column_types = [QVariant.Int, QVariant.Int, QVariant.Int, QVariant.Int, QVariant.Int,
            QVariant.String, QVariant.Double, QVariant.String, QVariant.String, QVariant.Double, 
            QVariant.String, QVariant.Double, QVariant.String, QVariant.Int, QVariant.Double,
            QVariant.Double, QVariant.String, QVariant.Int, QVariant.Int, QVariant.Int, 
            QVariant.Int, QVariant.Double, QVariant.Double, QVariant.String]
            
        self.column_stypes = ["integer", "integer", "integer", "integer", "integer", "string", 
            "double", "string", "string", "double", "string", "double", "string", "integer", "double", "double", "string", 
            "integer", "integer", "integer", "integer", "double", "double", "string"]
            
        self.col_len = [10, 10, 10, 10, 10, 1000, 20, 100, 100, 20, 100, 20, 100, 10, 20, 20, 100,
            10, 10, 10, 10, 20, 20, 100]

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SiliconSaber', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = SiliconSaberDialogBase()
        self.dlgcompute = SiliconSaberDialogCompute()
        self.dlgcreate = SiliconSaberDialogCreate()
        self.dlgimport = SiliconSaberDialogImport()
        self.dlgcommit = SiliconSaberDialogCommit()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path1 = ':/plugins/SiliconSaber/layers.png'
        icon_path2 = ':/plugins/SiliconSaber/calculator.png'
        icon_path3 = ':/plugins/SiliconSaber/export.png'
        icon_path4 = ':/plugins/SiliconSaber/database.png'
        icon_path5 = ':/plugins/SiliconSaber/import.png'
        
        self.add_action(
            icon_path1,
            text=self.tr(u'Create New Layer'),
            callback=self.create,
            parent=self.iface.mainWindow())
            
            
        self.add_action(
            icon_path2,
            text=self.tr(u'Calculate Attributes'),
            callback=self.compute,
            parent=self.iface.mainWindow())
        
        self.add_action(
            icon_path3,
            text=self.tr(u'Export Layer'),
            callback=self.export,
            parent=self.iface.mainWindow())
        
        self.add_action(
            icon_path4,
            text=self.tr(u'Commit to Main Table'),
            callback=self.commitlayer,
            parent=self.iface.mainWindow())
            
        self.add_action(
            icon_path5,
            text=self.tr(u'Import Table'),
            callback=self.importtable,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&SiliconSaber'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def export(self):
        """Run method that performs all the real work"""
        self.dlg.layerList.clear()
        layers = self.iface.legendInterface().layers()
        layer_list = []
        for layer in layers:
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer:
                layer_list.append(layer.name())
        self.dlg.layerList.addItems(layer_list)
        
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            
            selectedlayerindex = self.dlg.layerList.currentIndex()
            selectedLayer = layers[selectedlayerindex]
            layeruri = selectedLayer.dataProvider().dataSourceUri().split("|")[0]
            
            uri = "MSSQL:server=%s;database=%s;trusted_connection=yes" % (self.dlg.dbServer.text(), 
                  self.dlg.dbName.text())
            ogrstring = "ogr2ogr.exe -lco UPLOAD_GEOM_FORMAT=wkt -f MSSQLSpatial" + \
                        " \"%s\" \"%s\" -overwrite" % (uri, layeruri)
                        
            print(ogrstring)
            subprocess.call(ogrstring)

    def compute(self):
        """Run method that performs all the real work"""
        self.dlgcompute.layerList.clear()
        layers = self.iface.legendInterface().layers()
        layer_list = []
        for layer in layers:
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer:
                layer_list.append(layer.name())
        self.dlgcompute.layerList.addItems(layer_list)
        
        # show the dialog
        self.dlgcompute.show()
        # Run the dialog event loop
        result = self.dlgcompute.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            
            selectedlayerindex = self.dlgcompute.layerList.currentIndex()
            selectedLayer = layers[selectedlayerindex]
            
            pr = selectedLayer.dataProvider()
            caps = pr.capabilities()
            
            fieldnames = [field.name() for field in pr.fields()]
            print(fieldnames)
            
            for col_idx in range(0, len(self.column_names)):
                if fieldnames[col_idx] not in fieldnames:
                    field = QgsField(self.column_names[col_idx], self.column_types[col_idx], 
                            self.column_stypes[col_idx], self.col_len[col_idx], 3)
                    pr.addAttributes([field])
                
            selectedLayer.updateFields()
            
            selectedLayer.startEditing()
            count = 0
            for feat in selectedLayer.getFeatures():
                count += 1
                id = feat.id()
                selectedLayer.changeAttributeValue(id, self.column_names.index("id"), count)
                selectedLayer.changeAttributeValue(id, self.column_names.index("vertices"), 
                    str(feat.geometry().asPolygon()[0]))
                selectedLayer.changeAttributeValue(id, self.column_names.index("area"), 
                    feat.geometry().area())
                selectedLayer.changeAttributeValue(id, self.column_names.index("length"), 
                    feat.geometry().length())
                selectedLayer.changeAttributeValue(id, self.column_names.index("centroid"), 
                    str(feat.geometry().centroid().asPoint()))
            
            selectedLayer.commitChanges()
            vlayerstring = "Polygon?crs=epsg:4326"
            vl = QgsVectorLayer(vlayerstring, "Layer 1", "memory")
            by_feature = True
            
            
            dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tempfiles",
                       "ombb.shp")
            selectedUri = selectedLayer.dataProvider().dataSourceUri().split("|")[0]
            
            print(selectedUri)
            print(dir_path)
            
            output = processing.runalg("qgis:orientedminimumboundingbox", selectedUri, by_feature,
                     dir_path)
            print(output)
            vl = QgsVectorLayer(dir_path, "OMBB Output", "ogr")
            
            selectedLayer.startEditing()
            for feat in vl.getFeatures():
                id = feat.id()
                selectedLayer.changeAttributeValue(id, self.column_names.index("ombb"), 
                    str(feat.geometry().asPolygon()[0]))
            
            selectedLayer.commitChanges()
            # QgsMapLayerRegistry.instance().addMapLayer(vl)
            
                
    def create(self):
        self.dlgcreate.layerList.clear()
        layer_list = ["Point", "LineString", "Polygon"]
        self.dlgcreate.layerList.addItems(layer_list)
        
        # show the dialog
        self.dlgcreate.show()
        # Run the dialog event loop
        result = self.dlgcreate.exec_()
        # See if OK was pressed
        
        filename = "temp_%d.shp" % self.count
        self.count += 1
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tempfiles", filename)

        if result:
            selectedvector = self.dlgcreate.layerList.currentText()
            vlayerstring = "%s?crs=epsg:4326" %  selectedvector
            vl = QgsVectorLayer(vlayerstring, "Layer %d" % self.count, "memory")
            
            pr = vl.dataProvider()
            
            fieldnames = [field.name() for field in pr.fields()]
            
            for col_idx in range(0, len(self.column_names)):
                if col_idx not in fieldnames:
                    field = QgsField(self.column_names[col_idx], self.column_types[col_idx], 
                            self.column_stypes[col_idx], self.col_len[col_idx], 3)
                    pr.addAttributes([field])
                
            vl.updateFields()
            
            if os.path.isfile(dir_path):
                os.remove(dir_path)
            
            error = QgsVectorFileWriter.writeAsVectorFormat(vl, dir_path, "CP1250", None, 
                        "ESRI Shapefile")
            
            vl = QgsVectorLayer(dir_path, "Layer %d" % self.count, "ogr")
            pr = vl.dataProvider()
            QgsMapLayerRegistry.instance().addMapLayer(vl)
            
    def importtable(self):
        print(dir(self.dlgimport))
        
        # show the dialog
        self.dlgimport.show()
        
        # Run the dialog event loop
        result = self.dlgimport.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            
            uri = "MSSQL:server=%s;database=%s;tables=%s;trusted_connection=yes" % (
                  self.dlgimport.dbServer.text(), self.dlgimport.dbName.text(), 
                  self.dlgimport.tableName.text())
            print(uri)
            QgsLogger.logMessageToFile(uri)
            vl = QgsVectorLayer(uri, self.dlgimport.tableName.text(), "ogr")
            print(vl.isValid())
            QgsMapLayerRegistry.instance().addMapLayer(vl)
            
            print(vl.dataProvider().capabilitiesString())
            
    def commitlayer(self):
        self.dlgcommit.layerList.clear()
        layers = self.iface.legendInterface().layers()
        layer_list = []
        for layer in layers:
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer:
                layer_list.append(layer.name())
        self.dlgcommit.layerList.addItems(layer_list)
        
        # show the dialog
        self.dlgcommit.show()
        # Run the dialog event loop
        result = self.dlgcommit.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            
            selectedlayerindex = self.dlgcommit.layerList.currentIndex()
            selectedLayer = layers[selectedlayerindex]
            layeruri = selectedLayer.dataProvider().dataSourceUri().split("|")[0]
            
            connstring = "DRIVER={ODBC Driver 13 for SQL Server}; SERVER=%s; DATABASE=%s; Trusted_Connection=yes;" % (self.dlgcommit.dbServer.text(), self.dlgcommit.dbName.text())
            print(connstring)
            conn = pyodbc.connect(connstring)
            
            getlastid = "SELECT Object_ID FROM %s ORDER BY Object_ID DESC;" % self.dlgcommit.tableName.text()
            row = conn.execute(getlastid).fetchone()
            if row is None:
                row = 0
            else:
                row = row[0]
            
            for feat in selectedLayer.getFeatures():
                attrs = feat.attributes()
                attrs[0] = attrs[0] + row
                print(attrs)
                attrs = [self.dlgcommit.tableName.text()] + attrs
                print(attrs)
                print(len(attrs[:-3]))
                insertstr = "INSERT INTO %s VALUES(%s,%s,%s,%s,%s,'%s',%s,%s,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);" % tuple(attrs[:-3])
                print(insertstr)
                error = conn.execute(insertstr)
                print(error)
            
            conn.commit()
            # for row in out:
                # print(row)
            
            