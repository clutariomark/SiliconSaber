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
from math import degrees, atan2

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
        
        self.drivers = [
            "SQL Server",
            "SQL Native Client",
            "SQL Server Native Client 10.0",
            "SQL Server Native Client 11.0",
            "ODBC Driver 11 for SQL Server",
            "ODBC Driver 13 for SQL Server",
        ]
        
        self.server = ""
        self.database = ""
        self.tables = []
        self.selecteddrivername = ""
        
        self.functionIndex = 0
        self.desc_columns = {}
        self.vals_columns = {}

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
        self.dlgconnect = SiliconSaberDialogConnect()

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
        icon_path6 = ':/plugins/SiliconSaber/link.png'
        icon_path7 = ':/plugins/SiliconSaber/data-network.png'
        
        
        self.add_action(
            icon_path7,
            text=self.tr(u'Connect Database'),
            callback=self.connect,
            parent=self.iface.mainWindow())
        
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
    
    def createfunctionid(self):
        desc_columns = self.desc_columns[self.tables[self.dlgcreate.functionTable.currentIndex()]]
        vals_columns = self.vals_columns[self.tables[self.dlgcreate.functionTable.currentIndex()]]
        self.dlgcreate.desc_col.clear()
        self.dlgcreate.val_col.clear()
        self.dlgcreate.desc_col.addItems(desc_columns)
        self.dlgcreate.val_col.addItems(vals_columns)
        
    def computefunctionid(self):
        desc_columns = self.desc_columns[self.tables[self.dlgcompute.functionTable.currentIndex()]]
        vals_columns = self.vals_columns[self.tables[self.dlgcompute.functionTable.currentIndex()]]
        self.dlgcompute.desc_col.clear()
        self.dlgcompute.val_col.clear()
        self.dlgcompute.desc_col.addItems(desc_columns)
        self.dlgcompute.val_col.addItems(vals_columns)
        
    def GetAngleOfLineBetweenTwoPoints(self, p1, p2, angle_unit="degrees"):
        xDiff = p2.x() - p1.x()
        yDiff = p2.y() - p1.y()
        if angle_unit == "radians":
            return atan2(yDiff, xDiff)
        else:
            return degrees(atan2(yDiff, xDiff))
        
    def OMBBox(self, geom):
        g = geom.convexHull()

        if g.type() != QGis.Polygon:
            return None, None, None, None, None, None
        r = g.asPolygon()[0]

        p0 = QgsPoint(r[0][0], r[0][1])

        i = 0
        l = len(r)
        OMBBox = QgsGeometry()
        gBBox = g.boundingBox()
        OMBBox_area = gBBox.height() * gBBox.width()
        OMBBox_angle = 0
        OMBBox_width = 0
        OMBBox_heigth = 0
        OMBBox_perim = 0
        while i < l - 1:
            x = QgsGeometry(g)
            angle = self.GetAngleOfLineBetweenTwoPoints(r[i], r[i + 1])
            x.rotate(angle, p0)
            bbox = x.boundingBox()
            bb = QgsGeometry.fromWkt(bbox.asWktPolygon())
            bb.rotate(-angle, p0)

            areabb = bb.area()
            if areabb <= OMBBox_area:
                OMBBox = QgsGeometry(bb)
                OMBBox_area = areabb
                OMBBox_angle = angle
                OMBBox_width = bbox.width()
                OMBBox_heigth = bbox.height()
                OMBBox_perim = 2 * OMBBox_width + 2 * OMBBox_heigth
            i += 1

        return OMBBox, OMBBox_area, OMBBox_perim, OMBBox_angle, OMBBox_width, OMBBox_heigth

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
        
        self.dlg.dbServer.setText(self.server)
        self.dlg.dbName.setText(self.database)
        
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
        
        connstring = "DRIVER={%s}; SERVER=%s; DATABASE=%s; Trusted_Connection=yes;" % (self.selecteddrivername, self.server, self.database)
        
        if self.selecteddrivername == "" or self.server == "" or self.database == "":
            self.iface.messageBar().pushMessage("WARNING", "Connect to database first!", 
                    level=QgsMessageBar.WARNING)
        else:
            conn = pyodbc.connect(connstring)
            
            self.dlgcompute.layerList.clear()
            layers = self.iface.legendInterface().layers()
            layer_list = []
            for layer in layers:
                layerType = layer.type()
                if layerType == QgsMapLayer.VectorLayer:
                    layer_list.append(layer.name())
            self.dlgcompute.layerList.addItems(layer_list)
            
            self.dlgcompute.functionTable.clear()
            self.dlgcompute.functionTable.addItems(self.tables)
            
            self.computefunctionid()       
        
            # show the dialog and wait if OK is pressed
            self.dlgcompute.show()
            
            self.dlgcompute.functionTable.currentIndexChanged.connect(self.computefunctionid)
            
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
                    
                    feat_id = []
                    for feat in selectedLayer.getFeatures():
                        count += 1
                        id = feat.id()
                        feat_id.append(id)
                        
                        if feat["ogc_fid"] is None:
                            selectedLayer.changeAttributeValue(id, 0, count)
                            
                        if selectedLayer.wkbType() == QGis.WKBPolygon:
                            selectedLayer.changeAttributeValue(id, self.column_names.index("vertices"), 
                                str(feat.geometry().asPolygon()[0]))

                            selectedLayer.changeAttributeValue(id, self.column_names.index("numVert"), 
                                len(feat.geometry().asPolygon()[0]))
                        
                        elif selectedLayer.wkbType() == QGis.WKBLineString:
                            selectedLayer.changeAttributeValue(id, self.column_names.index("vertices"), 
                                str(feat.geometry().asPolyline()))

                            selectedLayer.changeAttributeValue(id, self.column_names.index("numVert"), 
                                len(feat.geometry().asPolyline()))
                                
                        elif selectedLayer.wkbType() == QGis.WKBPoint:
                            selectedLayer.changeAttributeValue(id, self.column_names.index("vertices"), 
                                str(feat.geometry().asPoint()))

                            selectedLayer.changeAttributeValue(id, self.column_names.index("numVert"), 1)

                        selectedLayer.changeAttributeValue(id, self.column_names.index("centerGvt"), 
                            str(feat.geometry().centroid().asPoint()))
                        selectedLayer.changeAttributeValue(id, self.column_names.index("layer"), 
                            selectedLayer.name())
                        selectedLayer.changeAttributeValue(id, self.column_names.index("mapId"), 
                            project.fileName())
                        selectedLayer.changeAttributeValue(id, self.column_names.index("active"), 
                            1)
                        selectedLayer.changeAttributeValue(id, self.column_names.index("trnp"), 
                            50)
                        selectedLayer.changeAttributeValue(id, self.column_names.index("scaling"), 
                            1)
                        selectedLayer.changeAttributeValue(id, self.column_names.index("color"), 
                            str(color))
                            
                        ombb = self.OMBBox(feat.geometry())
                        
                        if ombb[0] is not None:
                            selectedLayer.changeAttributeValue(id, self.column_names.index("ombb"), 
                                str(ombb[0].asPolygon()[0]))
                            selectedLayer.changeAttributeValue(id, self.column_names.index("orient"),
                                ombb[3])
                    
                    selectedLayer.commitChanges()
                    
                    # Computation of OMBB
                    # by_feature = True
                    # dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tempfiles",
                               # "ombb.shp")
                    # selectedUri = selectedLayer.dataProvider().dataSourceUri().split("|")[0]
                    
                    # output = processing.runalg("qgis:orientedminimumboundingbox", selectedUri, by_feature,
                             # dir_path)
                        
                    table = self.tables[self.dlgcompute.functionTable.currentIndex()]
                    desc_col = self.desc_columns[table][self.dlgcompute.desc_col.currentIndex()]
                    val_col = self.vals_columns[table][self.dlgcompute.val_col.currentIndex()]
                    
                    selectstring = "SELECT %s, %s FROM %s;" % (desc_col, val_col, table)
                    
                    functions = conn.execute(selectstring)
            
                    valuemap = {}                    
                    for func in functions:                        
                        valuemap[func[0]] = func[1]
                    
                    valueindex = selectedLayer.fieldNameIndex("funcId")
                    selectedLayer.setEditorWidgetV2( valueindex, 'ValueMap' )
                    selectedLayer.setEditorWidgetV2Config( valueindex, valuemap )
                    selectedLayer.updateFields()
                
                    self.iface.messageBar().pushMessage("INFO", "Computation is done!", 
                        level=QgsMessageBar.INFO)
                except Exception, e:
                    print(e)
                    errormsg = "There is an error in the computation! %s" % str(e)
                    self.iface.messageBar().pushMessage("ERROR", errormsg, 
                        level=QgsMessageBar.CRITICAL)
                        
            conn.close()
                
    def create(self):
        connstring = "DRIVER={%s}; SERVER=%s; DATABASE=%s; Trusted_Connection=yes;" % (self.selecteddrivername, self.server, self.database)
        
        if self.selecteddrivername == "" or self.server == "" or self.database == "":
            self.iface.messageBar().pushMessage("WARNING", "Connect to database first!", 
                    level=QgsMessageBar.WARNING)
        else:
            conn = pyodbc.connect(connstring)
            
            self.dlgcreate.layerList.clear()
            layer_list = ["Point", "LineString", "Polygon"]
            self.dlgcreate.layerList.addItems(layer_list)
            self.dlgcreate.layerList.setCurrentIndex(2)
            
            self.dlgcreate.functionTable.clear()
            self.dlgcreate.functionTable.addItems(self.tables)
            
            self.createfunctionid()

            # File name for temporary shapefile
            cur_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tempfiles")
            os.chdir(cur_dir)
            files = [i for i in glob.glob('layer_*.shp')]
            self.count = len(files)
            self.count += 1
            
            layername = "Layer %d" % self.count
            self.dlgcreate.layerName.setText(layername)
            
            self.dlgcreate.show()
            
            self.dlgcreate.functionTable.currentIndexChanged.connect(self.createfunctionid)
            
            result = self.dlgcreate.exec_()
            
            if result:
                try:
                    self.functionIndex = self.dlgcreate.functionTable.currentIndex()
                    
                    layername = self.dlgcreate.layerName.text()
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
                                
                    error = QgsVectorFileWriter.writeAsVectorFormat(vl, dir_path, "utf-8", None,
                                "SQLite", False, None, ["SPATIALITE=YES",])
                    
                    vl = QgsVectorLayer(dir_path, self.dlgcreate.layerName.text(), "ogr")
                    pr = vl.dataProvider()
                    QgsMapLayerRegistry.instance().addMapLayer(vl)
                    
                    table = self.tables[self.dlgcreate.functionTable.currentIndex()]
                    desc_col = self.desc_columns[table][self.dlgcreate.desc_col.currentIndex()]
                    val_col = self.vals_columns[table][self.dlgcreate.val_col.currentIndex()]
                    
                    selectstring = "SELECT %s, %s FROM %s;" % (desc_col, val_col, table)
                    
                    functions = conn.execute(selectstring)
            
                    valuemap = {}                    
                    for func in functions:                        
                        valuemap[func[0]] = func[1]
                    
                    valueindex = vl.fieldNameIndex("funcId")
                    vl.setEditorWidgetV2( valueindex, 'ValueMap' )
                    vl.setEditorWidgetV2Config( valueindex, valuemap )
                    vl.updateFields()
                    
                    self.iface.messageBar().pushMessage("INFO", layername, 
                        level=QgsMessageBar.INFO)
                    
                except Exception, e:
                    errormsg = "Layer name/filename %s is already in the directory. Please provide a different name." % layername
                    print(e)
                    self.iface.messageBar().pushMessage("ERROR", errormsg, 
                        level=QgsMessageBar.CRITICAL)
            conn.close()
            
    def importtable(self):     
        
        if self.selecteddrivername == "" or self.server == "" or self.database == "":
            self.iface.messageBar().pushMessage("WARNING", "Connect to database first!", 
                    level=QgsMessageBar.WARNING)
        else:
            connstring = "DRIVER={%s}; SERVER=%s; DATABASE=%s; Trusted_Connection=yes;" % (self.selecteddrivername, self.server, self.database)

            conn = pyodbc.connect(connstring)
            self.tables = []
            tables = conn.execute("SELECT TABLE_NAME FROM %s.INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';" % self.database).fetchall()
            for tab in tables:
                self.tables.append(tab[0])
            
            conn.commit()
            conn.close()
        
            self.dlgimport.tableName.clear()
            self.dlgimport.tableName.addItems(self.tables)
            self.dlgimport.tableName.setCurrentIndex(1)
            
            self.dlgimport.dbServer.setText(self.server)
            self.dlgimport.dbName.setText(self.database)
            
            self.dlgimport.show()
            result = self.dlgimport.exec_()
            
            if result:
                try:
                    
                    selectedtable = self.tables[self.dlgimport.tableName.currentIndex()]
                    uri = "MSSQL:server=%s;database=%s;tables=%s;trusted_connection=yes" % (
                          self.dlgimport.dbServer.text(), self.dlgimport.dbName.text(), 
                          selectedtable)

                    vl = QgsVectorLayer(uri, selectedtable, "ogr")                
                    
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
                    
                    
    def connect(self):
        self.dlgconnect.driverList.clear()
        self.dlgconnect.driverList.addItems(self.drivers)
        self.dlgconnect.driverList.setCurrentIndex(3)
        self.tables = []
        
        self.dlgconnect.show()
        result = self.dlgconnect.exec_()
        
        if result:
            try:
                self.selecteddrivername = self.drivers[self.dlgconnect.driverList.currentIndex()]
                self.server = self.dlgconnect.dbServer.text()
                self.database = self.dlgconnect.dbName.text()
                
                if self.selecteddrivername == "":
                    self.iface.messageBar().pushMessage("WARNING", "Please select a drivername.", 
                        level=QgsMessageBar.WARNING)
                elif self.server == "":
                    self.iface.messageBar().pushMessage("WARNING", "Please enter the database server.", 
                        level=QgsMessageBar.WARNING)
                elif self.database == "":
                    self.iface.messageBar().pushMessage("WARNING", "Please enter the database name.", 
                        level=QgsMessageBar.WARNING)
                else:
                    
                    connstring = "DRIVER={%s}; SERVER=%s; DATABASE=%s; Trusted_Connection=yes;" % (self.selecteddrivername, self.server, self.database)

                    conn = pyodbc.connect(connstring)
                    
                    tables = conn.execute("SELECT TABLE_NAME FROM %s.INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';" % self.database).fetchall()
                    
                    conn.commit()
                    
                    for tab in tables:
                        self.tables.append(tab[0])
                        self.desc_columns[tab[0]] = []
                        self.vals_columns[tab[0]] = []
                        colstring = "SELECT COLUMN_NAME, DATA_TYPE FROM %s.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '%s';" % (self.database, tab[0])
                        cols = conn.execute(colstring).fetchall()
                        conn.commit()
                        for col in cols:
                            if col[1] == u'nvarchar':
                                self.desc_columns[tab[0]].append(col[0])
                            elif col[1] == u'int':
                                self.vals_columns[tab[0]].append(col[0])
                    
                    conn.close()
                    self.iface.messageBar().pushMessage("INFO", "Connected to %s database" % self.database, 
                        level=QgsMessageBar.INFO)
            
            except Exception, e:
                print(str(e))
                errormsg = "Connection Failed!"
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
        
        self.dlgcommit.driverList.addItems(self.drivers)
        self.dlgcommit.driverList.setCurrentIndex(3)
        
        self.dlgcommit.dbName.setText(self.database)
        self.dlgcommit.dbServer.setText(self.server)
        self.dlgcommit.tableName.setText("MapObjects")
        
        self.dlgcommit.show()
        result = self.dlgcommit.exec_()
        if result:
            try:
                selectedlayerindex = self.dlgcommit.layerList.currentIndex()
                selectedLayer = layers[selectedlayerindex]
                layeruri = selectedLayer.dataProvider().dataSourceUri().split("|")[0]
                
                selecteddriver = self.drivers[self.dlgcommit.driverList.currentIndex()]
                connstring = "DRIVER={%s}; SERVER=%s; DATABASE=%s; Trusted_Connection=yes;" % (selecteddriver, self.dlgcommit.dbServer.text(), self.dlgcommit.dbName.text())
                conn = pyodbc.connect(connstring)
                    
                cols = ["Map_ID", "Object_Level", 
                    "Object_Active", "Object_Vertices", "Object_NumVertices",
                    "Object_Elev", "Object_Center_Gvt", "Object_OMBB", "Object_Orientation",
                    "Object_Descriptor", "Object_Access", "Object_Color", "Object_Trnp", 
                    "Object_Outline", "Object_Scaling", "Object_Name", "Object_Number",
                    "Object_Geo_ID", "Object_Role_ID", "Object_Func_ID"]
                
                updated = []
                for feat in selectedLayer.getFeatures():
                    attrs = feat.attributes()
                    id = attrs[0]
                    layer = attrs[2]
                    primary_key = (self.dlgcommit.tableName.text(), id, layer)
                    sql_string = "SELECT Object_ID, Object_Layer FROM %s WHERE Object_ID = %d and Object_Layer = '%s';" % primary_key
                    row = conn.execute(sql_string).fetchone()

                    if row is None:
                        attrs = [self.dlgcommit.tableName.text()] + attrs
                        stringcols = [2,3,6,9,10,14,18]
                        for col in stringcols:
                            if attrs[col] != NULL:
                                attrs[col] = "'%s'" % attrs[col]
                        insertstr = "INSERT INTO %s VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);" % tuple(attrs)   
                        error = conn.execute(insertstr)

                    else:
                        updatestr = "UPDATE %s SET " % self.dlgcommit.tableName.text()
                        del attrs[0]
                        del attrs[1]
                        
                        stringcols = [0,3,6,7,11]
                        
                        for i in range(0, len(attrs)):
                            if i in stringcols:
                                attrs[i] = "'%s'" % attrs[i]
                            updatestr = updatestr + "%s = %s" % (cols[i], attrs[i])
                            if i == len(attrs)-1:
                                updatestr = updatestr + " "
                            else:
                                updatestr = updatestr + ", "
                        
                        updatestr = updatestr + "WHERE Object_ID = %d and Object_Layer = '%s';" % (id, layer)
                        primary_key = list(primary_key)
                        primary_key.pop(0)
                        updated.append(primary_key)
                        error = conn.execute(updatestr)
                
                test = str(updated)
                if len(updated) != 0:
                    warningstring = ""
                    for item in updated:
                        warningstring = warningstring + "ID: %d, Layer: %s was updated\n" % tuple(item)
                        
                    self.iface.messageBar().pushMessage("WARNING", "The following features already exist! %s " % warningstring,  
                        level=QgsMessageBar.WARNING)
                        
                conn.commit()
                conn.close()
                
                self.iface.messageBar().pushMessage("INFO", "Commit to main table is successful!", 
                    level=QgsMessageBar.INFO)
            except Exception, e:
                errormsg = "Commit to main table failed! %s" % str(e)
                self.iface.messageBar().pushMessage("ERROR", errormsg, 
                    level=QgsMessageBar.CRITICAL)