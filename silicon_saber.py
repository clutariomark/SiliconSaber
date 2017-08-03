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
from qgis.gui import QgsMessageBar
import subprocess
import os, sys
import pyodbc
import glob

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
        
        self.column_names = ["id", "mapId", "layer", "level", "active", "vertices", "numVert", "elev",
            "centerGvt", "ombb", "orient", "desc", "access", "color", "trnp", "outline", "scaling", 
            "name", "number", "geoId", "roleId", "funcId"]
            # , "area", "length"]
            
        self.column_types = [QVariant.Int, QVariant.String, QVariant.String, QVariant.Int, QVariant.Int,
            QVariant.String, QVariant.Int, QVariant.Double, QVariant.String, QVariant.String, QVariant.Double, 
            QVariant.String, QVariant.Double, QVariant.String, QVariant.Int, QVariant.Double,
            QVariant.Double, QVariant.String, QVariant.Int, QVariant.Int, QVariant.Int, 
            QVariant.Int]
            # , QVariant.Double, QVariant.Double]
            
        self.column_stypes = ["integer", "string", "string", "integer", "integer", "string", "integer",
            "double", "string", "string", "double", "string", "double", "string", "integer", "double", "double", "string", 
            "integer", "integer", "integer", "integer", "double"]
            # , "double", "string"]
            
        self.col_len = [10, 100, 100, 10, 10, 254, 10, 20, 100, 254, 20, 100, 20, 100, 10, 20, 20, 100,
            10, 10, 10, 10]
            # , 20, 20]

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
        self.dlg.layerList.clear()
        layers = self.iface.legendInterface().layers()
        layer_list = []
        for layer in layers:
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer:
                layer_list.append(layer.name())
        self.dlg.layerList.addItems(layer_list)
        
        self.dlg.show()
        result = self.dlg.exec_()
        
        if result:
            try:
                selectedlayerindex = self.dlg.layerList.currentIndex()
                selectedLayer = layers[selectedlayerindex]
                layeruri = selectedLayer.dataProvider().dataSourceUri().split("|")[0]
                
                uri = "MSSQL:server=%s;database=%s;trusted_connection=yes" % (self.dlg.dbServer.text(), 
                      self.dlg.dbName.text())
                ogrstring = "ogr2ogr.exe -lco UPLOAD_GEOM_FORMAT=wkt -f MSSQLSpatial" + \
                            " \"%s\" \"%s\" -overwrite" % (uri, layeruri)
                            
                subprocess.call(ogrstring)
                self.iface.messageBar().pushMessage("INFO", "Export was successful!", 
                    level=QgsMessageBar.INFO)
                    
            except Exception, e:
                errormsg = "Export table failed! %s" % str(e)
                self.iface.messageBar().pushMessage("ERROR", errormsg, 
                    level=QgsMessageBar.CRITICAL)
                

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
        
        # show the dialog and wait if OK is pressed
        self.dlgcompute.show()
        result = self.dlgcompute.exec_()

        if result:
            try:
                selectedlayerindex = self.dlgcompute.layerList.currentIndex()
                selectedLayer = layers[selectedlayerindex]
                
                pr = selectedLayer.dataProvider()
                
                fieldnames = [field.name() for field in pr.fields()]
                
                # Create fields if not yet there
                for col_idx in range(0, len(self.column_names)):
                    if fieldnames[col_idx] not in fieldnames:
                        field = QgsField(self.column_names[col_idx], self.column_types[col_idx], 
                                self.column_stypes[col_idx], self.col_len[col_idx], 3)
                        pr.addAttributes([field])
                    
                selectedLayer.updateFields()
                
                # Update attribute value per feature
                selectedLayer.startEditing()
                count = 0
                
                project = QgsProject.instance()
                color = selectedLayer.rendererV2().symbols()[0].color().getRgb()
                # print(color)
                # symbol.setColor(QColor.fromRgb(50,50,250))
                
                
                for feat in selectedLayer.getFeatures():
                    count += 1
                    id = feat.id()
                    # if feat["id"] is not None:
                        # selectedLayer.changeAttributeValue(id, self.column_names.index("id"), count)
                    if feat["ogc_fid"] is not None:
                        selectedLayer.changeAttributeValue(id, 0, count)
                    selectedLayer.changeAttributeValue(id, self.column_names.index("vertices"), 
                        str(feat.geometry().asPolygon()[0]))
                    # print(len(str(feat.geometry().asPolygon()[0])))
                    selectedLayer.changeAttributeValue(id, self.column_names.index("numVert"), 
                        len(feat.geometry().asPolygon()[0]))
                    # selectedLayer.changeAttributeValue(id, self.column_names.index("area"), 
                        # feat.geometry().area())
                    # selectedLayer.changeAttributeValue(id, self.column_names.index("length"), 
                        # feat.geometry().length())
                    selectedLayer.changeAttributeValue(id, self.column_names.index("centerGvt"), 
                        str(feat.geometry().centroid().asPoint()))
                    selectedLayer.changeAttributeValue(id, self.column_names.index("layer"), 
                        selectedLayer.name())
                    selectedLayer.changeAttributeValue(id, self.column_names.index("mapId"), 
                        project.fileName())
                    selectedLayer.changeAttributeValue(id, self.column_names.index("active"), 
                        True)
                    selectedLayer.changeAttributeValue(id, self.column_names.index("trnp"), 
                        50)
                    selectedLayer.changeAttributeValue(id, self.column_names.index("scaling"), 
                        1)
                    selectedLayer.changeAttributeValue(id, self.column_names.index("color"), 
                        str(color))
                
                selectedLayer.commitChanges()
                
                # Computation of OMBB
                by_feature = True
                dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tempfiles",
                           "ombb.shp")
                selectedUri = selectedLayer.dataProvider().dataSourceUri().split("|")[0]
                
                output = processing.runalg("qgis:orientedminimumboundingbox", selectedUri, by_feature,
                         dir_path)
                         
                vl = QgsVectorLayer(dir_path, "OMBB Output", "ogr")
                
                selectedLayer.startEditing()
                for feat in vl.getFeatures():
                    id = feat.id() + 1
                    selectedLayer.changeAttributeValue(id, self.column_names.index("ombb"), 
                        str(feat.geometry().asPolygon()[0]))
                    selectedLayer.changeAttributeValue(id, self.column_names.index("orient"),
                        feat["ANGLE"])
                    # print(id, feat["ANGLE"])

                selectedLayer.commitChanges()
            
                # QgsMapLayerRegistry.instance().addMapLayer(vl)
                self.iface.messageBar().pushMessage("INFO", "Computation is done!", 
                    level=QgsMessageBar.INFO)
            except Exception, e:
                errormsg = "There is an error in the computation! %s" % str(e)
                self.iface.messageBar().pushMessage("ERROR", errormsg, 
                    level=QgsMessageBar.CRITICAL)
                
    def create(self):
        self.dlgcreate.layerList.clear()
        layer_list = ["Point", "LineString", "Polygon"]
        self.dlgcreate.layerList.addItems(layer_list)
        
        # File name for temporary shapefile
        cur_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tempfiles")
        os.chdir(cur_dir)
        files = [i for i in glob.glob('layer_*.shp')]
        self.count = len(files)
        self.count += 1
        
        layername = "Layer %d" % self.count
        self.dlgcreate.layerName.setText(layername)
        
        self.dlgcreate.show()
        
        result = self.dlgcreate.exec_()
        
        if result:
            try:
                # filename = "%s.shp" % self.dlgcreate.layerName.text().replace(" ", "_").lower()
                filename = "%s.sqlite" % self.dlgcreate.layerName.text().replace(" ", "_").lower()
                dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tempfiles", filename)
                
                # Create temporary layer in memory
                selectedvector = self.dlgcreate.layerList.currentText()
                vlayerstring = "%s?crs=epsg:4326" %  selectedvector
                vl = QgsVectorLayer(vlayerstring, layername, "memory")
                
                # Create fields if not yet there
                pr = vl.dataProvider()
                fieldnames = [field.name() for field in pr.fields()]
                for col_idx in range(0, len(self.column_names)):
                    if col_idx == 0:
                        pass
                    else:
                        if col_idx not in fieldnames:
                            field = QgsField(self.column_names[col_idx], self.column_types[col_idx], 
                                    self.column_stypes[col_idx], self.col_len[col_idx], 3)
                            pr.addAttributes([field])
                vl.updateFields()
                
                if os.path.isfile(dir_path):
                    os.remove(dir_path)
                
                # Save memory layer as shapefile
                # error = QgsVectorFileWriter.writeAsVectorFormat(vl, dir_path, "CP1250", None, 
                            # "ESRI Shapefile")
                            
                error = QgsVectorFileWriter.writeAsVectorFormat(vl, dir_path, "utf-8", None,
                            "SQLite", False, None, ["SPATIALITE=YES",])
                
                vl = QgsVectorLayer(dir_path, self.dlgcreate.layerName.text(), "ogr")
                # print(vl.name())
                pr = vl.dataProvider()
                QgsMapLayerRegistry.instance().addMapLayer(vl)
                self.iface.messageBar().pushMessage("INFO", layername, 
                    level=QgsMessageBar.INFO)
                
            except Exception, e:
                errormsg = "Layer name/filename %s is already in the directory. Please provide a different name." % layername
                self.iface.messageBar().pushMessage("ERROR", errormsg, 
                    level=QgsMessageBar.CRITICAL)
            
    def importtable(self):     
        self.dlgimport.show()
        result = self.dlgimport.exec_()
        if result:
            try:
                uri = "MSSQL:server=%s;database=%s;tables=%s;trusted_connection=yes" % (
                      self.dlgimport.dbServer.text(), self.dlgimport.dbName.text(), 
                      self.dlgimport.tableName.text())

                vl = QgsVectorLayer(uri, self.dlgimport.tableName.text(), "ogr")                
                
                if vl.isValid():
                    self.iface.messageBar().pushMessage("INFO", "Import table is successful!", 
                        level=QgsMessageBar.INFO)
                    QgsMapLayerRegistry.instance().addMapLayer(vl)
                else:
                    self.iface.messageBar().pushMessage("ERROR", "Import table failed!", 
                        level=QgsMessageBar.CRITICAL)
            
            except Exception, e:
                errormsg = "Import table failed! %s" % str(e)
                self.iface.messageBar().pushMessage("ERROR", errormsg, 
                    level=QgsMessageBar.CRITICAL)
            
    def commitlayer(self):
        self.dlgcommit.layerList.clear()
        self.dlgcommit.driverList.clear()
        layers = self.iface.legendInterface().layers()
        layer_list = []
        for layer in layers:
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer:
                layer_list.append(layer.name())
        self.dlgcommit.layerList.addItems(layer_list)
        
        drivers = [
            "SQL Server",
            "SQL Native Client",
            "SQL Server Native Client 10.0",
            "SQL Server Native Client 11.0",
            "ODBC Driver 11 for SQL Server",
            "ODBC Driver 13 for SQL Server",
        ]
        self.dlgcommit.driverList.addItems(drivers)
        self.dlgcommit.driverList.setCurrentIndex(5)
        
        self.dlgcommit.show()
        result = self.dlgcommit.exec_()
        if result:
            try:
                selectedlayerindex = self.dlgcommit.layerList.currentIndex()
                selectedLayer = layers[selectedlayerindex]
                layeruri = selectedLayer.dataProvider().dataSourceUri().split("|")[0]
                
                selecteddriver = drivers[self.dlgcommit.driverList.currentIndex()]
                connstring = "DRIVER={%s}; SERVER=%s; DATABASE=%s; Trusted_Connection=yes;" % (selecteddriver, self.dlgcommit.dbServer.text(), self.dlgcommit.dbName.text())
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
                    attrs = [self.dlgcommit.tableName.text()] + attrs
                    stringcols = [2,3,6,9,10,14,18]
                    # print(attrs)
                    for col in stringcols:
                        if attrs[col] != NULL:
                            attrs[col] = "'%s'" % attrs[col]
                        
                    print(attrs)
                    insertstr = "INSERT INTO %s VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);" % tuple(attrs)                    
                    # [:-3])
                    print(insertstr)
                    error = conn.execute(insertstr)

                conn.commit()
                
                self.iface.messageBar().pushMessage("INFO", "Commit to main table is successful!", 
                    level=QgsMessageBar.INFO)
                self.iface.messageBar().pushMessage("INFO", connstring, 
                    level=QgsMessageBar.INFO)
            except Exception, e:
                errormsg = "Commit to main table failed! %s" % str(e)
                self.iface.messageBar().pushMessage("ERROR", errormsg, 
                    level=QgsMessageBar.CRITICAL)