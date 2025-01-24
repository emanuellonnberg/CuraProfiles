#-----------------------------------------------------------------------------------------------------------------------------------------
# Copyright (c) 2022 5axes
# Initial Source from Johnny Matthews https://github.com/johnnygizmo/CuraSettingsWriter 
# The HTML plugin is released under the terms of the AGPLv3 or higher.
#-----------------------------------------------------------------------------------------------------------------------------------------
#
# Version 1.0.3 : simplify the source code with WriteTd
#               : Export also the meshfix paramater section by extruder and complementary information on extruder for machine definition
# Version 1.0.4 : html cleanup, no jquery dependency  thanks to https://github.com/etet100
# Version 1.0.5 : for configuration with multi extruder export the right extrudeur position and the information concerning the enabled
# Version 1.0.6 : table width='100%'
# Version 1.0.7 : Set in green variable modified in the top stack ( User modification )
# Version 1.0.8 : Option are now also translated
# Version 1.1.0 : New Top_Bottom category (for Beta and Master)
# Version 1.1.1 : Machine_manager.activeIntentCategory if Intent is used ( Ultimaker Machine)
# Version 1.1.2 : Bug correction with Arachne beta release
# Version 1.1.3 : Add Filament Cost / Material usage
#
# Version 2.0.0 : Version 5.0
# Version 2.0.1 : Export Experiental settings by extruder
# Version 2.0.2 : Export PRice for multi extruder
# Version 2.1.0 : Translate in French
# Version 2.1.1 : Add Embbeded ScreenShot ! tested on Chrome / IE and Edge  Comaptibility of the Code Cura 4.10
# Version 2.1.2 : Add PostProcessing Script Infos + Solved User modification issue
# Version 2.1.3 : Change location i18n
# Version 2.1.4 : Orange Background for not translated Parameters ( Supposed to be new parameters in the case of Alpha versions or Plugins )
#-----------------------------------------------------------------------------------------------------------------------------------------
import os
import platform
import html
import configparser  # The script lists are stored in metadata as serialised config files.

from datetime import datetime
from typing import cast, Dict, List, Optional, Tuple, Any, Set

USE_QT5 = False
try:
    from PyQt6.QtCore import Qt, QObject, QBuffer
except ImportError:
    from PyQt5.QtCore import Qt, QObject, QBuffer
    USE_QT5 = True
    
    
from cura.CuraApplication import CuraApplication
from UM.Workspace.WorkspaceWriter import WorkspaceWriter
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Qt.Duration import DurationFormat
from UM.Preferences import Preferences

from cura.CuraVersion import CuraVersion  # type: ignore
from cura.Utils.Threading import call_on_qt_thread
from cura.Snapshot import Snapshot
from UM.Version import Version

from UM.Resources import Resources
from UM.i18n import i18nCatalog

i18n_cura_catalog = i18nCatalog("cura")
i18n_catalog = i18nCatalog("fdmprinter.def.json")
i18n_extrud_catalog = i18nCatalog("fdmextruder.def.json")

from UM.Logger import Logger
from UM.Message import Message

encode = html.escape

Resources.addSearchPath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)),'resources')
)  # Plugin translation file import

catalog = i18nCatalog("curasettings")

if catalog.hasTranslationLoaded():
    Logger.log("i", "Cura Settings Writter Plugin translation loaded!")
    
class HtmlCuraSettings(WorkspaceWriter):

    def write(self, stream, nodes, mode = WorkspaceWriter.OutputMode.TextMode):
    
        # Current File path
        # Logger.log("d", "stream = %s", os.path.abspath(stream.name))

        self.Major=1
        self.Minor=0

        # Logger.log('d', "Info Version CuraVersion --> " + str(Version(CuraVersion)))
        Logger.log('d', "Info CuraVersion --> " + str(CuraVersion))
        
        # Test version for Cura Master
        # https://github.com/smartavionics/Cura
        if "master" in CuraVersion :
            self.Major=4
            self.Minor=20
        else:
            try:
                self.Major = int(CuraVersion.split(".")[0])
                self.Minor = int(CuraVersion.split(".")[1])
            except:
                pass
            
        
        stream.write("""<!DOCTYPE html>
            <meta charset='UTF-8'>
            <head>
                <title>Cura Settings Export</title>
                <style>
                    tr.category td { font-size: 1.1em; background-color: rgb(142,170,219); }
                    tr.disabled td { background-color: #eaeaea; color: #717171; }
                    tr.local td { background-color: #77DD77; }
                    body.hide-disabled tr.disabled { display: none; }
                    body.hide-local tr.normal { display: none; }
                    .val { width: 200px; text-align: right; }
                    .w-10 { width: 10%; }
                    .w-50 { width: 50%; }
                    .w-70 { width: 70%; }
                    .w-70o { width: 70%; background-color: #FFA500; }
                    .pl-l { padding-left: 20px; }
                    .pl-2 { padding-left: 40px; }
                    .pl-3 { padding-left: 60px; }
                    .pl-4 { padding-left: 80px; }
                    .pl-5 { padding-left: 100px; }
                </style>
            </head>
            <body lang=EN>
        \n""")
        
        machine_manager = CuraApplication.getInstance().getMachineManager()        
        stack = CuraApplication.getInstance().getGlobalContainerStack()

        #global_stack = machine_manager.activeMachine
        global_stack = CuraApplication.getInstance().getGlobalContainerStack()

        self._modified_global_param =[]
        # modified paramater       
        top_of_stack = cast(InstanceContainer, global_stack.getTop())  # Cache for efficiency.
        self._modified_global_param = top_of_stack.getAllKeys()
        
        TitleTxt = catalog.i18nc("@label","Print settings")
        ButtonTxt = catalog.i18nc("@action:label","Visible settings")
        ButtonTxt2 = catalog.i18nc("@action:label","User Modifications")

        stream.write("<h1>" + TitleTxt + "</h1>\n")
        stream.write("<button id='enabled'>" + ButtonTxt + "</button><P>\n")
        stream.write("<button id='local'>" + ButtonTxt2 + "</button><P>\n")

        # Script       
        stream.write("""<script>
                            var enabled = document.getElementById('enabled');
                            enabled.addEventListener('click', function() {
                                document.body.classList.toggle('hide-disabled');
                            });
                        </script>\n""")
        stream.write("""<script>
                            var local = document.getElementById('local');
                            local.addEventListener('click', function() {
                                document.body.classList.toggle('hide-local');
                            });
                        </script>\n""")
                        
        #Get extruder count
        extruder_count=stack.getProperty("machine_extruder_count", "value")
        print_information = CuraApplication.getInstance().getPrintInformation()
        
        stream.write("<table width='100%' border='1' cellpadding='3'>")
        # Job
        self._WriteTd(stream,catalog.i18nc("@label","Job Name"),print_information.jobName)

        # Attempt to add a thumbnail
        snapshot = self._createSnapshot()
        if snapshot:
            thumbnail_buffer = QBuffer()
            
            if USE_QT5:
                thumbnail_buffer.open(QBuffer.ReadWrite)
            else:
                thumbnail_buffer.open(QBuffer.OpenModeFlag.ReadWrite)
                    
            snapshot.save(thumbnail_buffer, "PNG")
            encodedSnapshot = thumbnail_buffer.data().toBase64().data().decode("utf-8")

            # thumbnail_file = zipfile.ZipInfo(THUMBNAIL_PATH)
            # Don't try to compress snapshot file, because the PNG is pretty much as compact as it will get
            # archive.writestr(thumbnail_file, thumbnail_buffer.data()) 
            # Logger.log("d", "stream = {}".format(encodedSnapshot))
            stream.write("<tr><td colspan='3'><center><img src='data:image/png;base64," + str(encodedSnapshot)+ "' width='300' height='300' alt='" + print_information.jobName + "' title='" + print_information.jobName + "' /></cente></td></tr>" )            
        
        self.cura_locale = CuraApplication.getInstance().getPreferences().getValue("general/language")
        
        # File
        # self._WriteTd(stream,"File",os.path.abspath(stream.name))
        # Date
        self._WriteTd(stream,"Date",datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        # platform
        self._WriteTd(stream,"Os",str(platform.system()) + " " + str(platform.version()))
        # language
        self._WriteTd(stream,"Language",str(self.cura_locale))
        
        # Version  
        self._WriteTd(stream,"Cura Version",CuraVersion)
            
        # Profile || Intent for Ultimaker Machine
        P_Name = global_stack.qualityChanges.getMetaData().get("name", "")
        if P_Name=="empty":
            P_Name = machine_manager.activeIntentCategory
            self._WriteTd(stream,catalog.i18nc("@label","Intent"),P_Name)
        else:
            self._WriteTd(stream,catalog.i18nc("@label","Profile"),P_Name)
        
        # Quality
        Q_Name = global_stack.quality.getMetaData().get("name", "")
        self._WriteTd(stream,catalog.i18nc("@label:table_header","Quality"),Q_Name)
                
        # Material
        # extruders = list(global_stack.extruders.values())  
        extruder_stack = CuraApplication.getInstance().getExtruderManager().getActiveExtruderStacks()       

        for Extrud in extruder_stack:
            PosE = int(Extrud.getMetaDataEntry("position"))
            PosE += 1
            
            M_Name = Extrud.material.getMetaData().get("material", "")
            
            MaterialStr="%s %s : %d"%(catalog.i18nc("@label", "Material"),catalog.i18nc("@label", "Extruder"),PosE)
            self._WriteTd(stream,MaterialStr,M_Name)
            
            if extruder_count>1:
                M_Enabled = Extrud.getMetaDataEntry("enabled")
                EnabledStr="%s %s : %d"%(catalog.i18nc("@label", "Extruder"),catalog.i18nc("@label", "Enabled"),PosE)
                self._WriteTd(stream,EnabledStr,M_Enabled)
            
        MAterial=0
        #   materialWeights
        for Mat in list(print_information.materialWeights):
            MAterial=MAterial+Mat
        if MAterial>0:
            M_Weight= "{:.1f} g".format(MAterial).rstrip("0").rstrip(".")
            self._WriteTd(stream,catalog.i18nc("@label","Material estimation"),M_Weight)
            # self._WriteTd(stream,catalog.i18nc("@label","Filament weight"),str(print_information.materialWeights)) 
            M_Length= str(print_information.materialLengths).rstrip("]").lstrip("[")
            
            M_Length="{0:s} m".format(M_Length)
            self._WriteTd(stream,catalog.i18nc("@text","Material usage"),M_Length)
            
            original_preferences = CuraApplication.getInstance().getPreferences() #Copy only the preferences that we use to the workspace.
            Currency = original_preferences.getValue("cura/currency")
            price=str(print_information.materialCosts).rstrip("]").lstrip("[")
            # Logger.log("d", "Currency = %s",Currency)
            # Logger.log("d", "price = %s",Currency)
            # Logger.log("d", "materialCosts = %s",print_information.materialCosts)
            
            if "," in price :
                M_Price= price.replace(',',Currency) + Currency
                self._WriteTd(stream,catalog.i18nc("@label","Filament Cost"),M_Price)            
            else :
                M_Price= str(round(float(price),2)) + " " + Currency
                self._WriteTd(stream,catalog.i18nc("@label","Filament Cost"),M_Price)
            
            #   Print time
            P_Time = catalog.i18nc("@text","%d D %d H %d Mn")%(print_information.currentPrintTime.days,print_information.currentPrintTime.hours,print_information.currentPrintTime.minutes)
            self._WriteTd(stream,catalog.i18nc("@label","Printing Time"),P_Time)   
            # self._WriteTd(stream,catalog.i18nc("@label","Print time"),str(print_information.currentPrintTime.getDisplayString(DurationFormat.Format.ISO8601)))
        
        
        # Define every section to get the same order as in the Cura Interface
        # Modification from global_stack to extruders[0]
        if extruder_count>1 :
            i=0
            # for Extrud in list(global_stack.extruders.values()):
            for Extrud in extruder_stack :       
                i += 1                        
                self._doTree(Extrud,"resolution",stream,0,i)
                # Shell before 4.9 and now walls
                self._doTree(Extrud,"shell",stream,0,i)
                # New section Arachne and 4.9 ?
                if self.Major > 4 or ( self.Major == 4 and self.Minor >= 9 ) :
                    self._doTree(Extrud,"top_bottom",stream,0,i)

                self._doTree(Extrud,"infill",stream,0,i)
                self._doTree(Extrud,"material",stream,0,i)
                self._doTree(Extrud,"speed",stream,0,i)
                self._doTree(Extrud,"travel",stream,0,i)
                self._doTree(Extrud,"cooling",stream,0,i)

                self._doTree(Extrud,"dual",stream,0,i)
        else:
            self._doTree(extruder_stack[0],"resolution",stream,0,0)
            # Shell before 4.9 and now walls
            self._doTree(extruder_stack[0],"shell",stream,0,0)
            # New section Arachne and 4.9 ?
            if self.Major > 4 or ( self.Major == 4 and self.Minor >= 9 ) :
                self._doTree(extruder_stack[0],"top_bottom",stream,0,0)

            self._doTree(extruder_stack[0],"infill",stream,0,0)
            self._doTree(extruder_stack[0],"material",stream,0,0)
            self._doTree(extruder_stack[0],"speed",stream,0,0)
            self._doTree(extruder_stack[0],"travel",stream,0,0)
            self._doTree(extruder_stack[0],"cooling",stream,0,0)

        self._doTree(extruder_stack[0],"support",stream,0,0)
        self._doTree(extruder_stack[0],"platform_adhesion",stream,0,0)
        
        if extruder_count>1 :
            i=0
            for Extrud in extruder_stack:
                i += 1
                self._doTree(Extrud,"meshfix",stream,0,i)    
                self._doTree(Extrud,"blackmagic",stream,0,i)  
                self._doTree(Extrud,"experimental",stream,0,i)
        else:
            self._doTree(extruder_stack[0],"meshfix",stream,0,0)    
            self._doTree(extruder_stack[0],"blackmagic",stream,0,0)  
            self._doTree(extruder_stack[0],"experimental",stream,0,0)       
        
        self._doTree(extruder_stack[0],"machine_settings",stream,0,0)
        
        i=0
        for Extrud in extruder_stack:
            i += 1
            self._doTreeExtrud(Extrud,"machine_settings",stream,0,i)

        # This Method is smarter but unfortunatly settings are not in the same ordrer as the Cura interface
        # for key in global_stack.getAllKeys():
        #     if global_stack.getProperty(key,"enabled") == True:
        #         if global_stack.getProperty(key,"type") == "category":
        #             self._doTree(global_stack,key,stream,0)

        #----------------------------------------
        #  Add Script List in the HTML Log File
        #----------------------------------------
        script_list = []
        scripts_list = global_stack.getMetaDataEntry("post_processing_scripts")
        if scripts_list :
            stream.write("<tr class='category'>")
            stream.write("<td colspan='3'>" + catalog.i18nc("@label","Postprocessing Scripts") + "</td>")
            stream.write("</tr>\n")        
            for script_str in scripts_list.split("\n"):  # Encoded config files should never contain three newlines in a row. At most 2, just before section headers.
                        if not script_str:  # There were no scripts in this one (or a corrupt file caused more than 3 consecutive newlines here).
                            continue
                        script_str = script_str.replace(r"\\\n", "\n").replace(r"\\\\", "\\\\")  # Unescape escape sequences.
                        script_parser = configparser.ConfigParser(interpolation=None)
                        script_parser.optionxform = str  # type: ignore  # Don't transform the setting keys as they are case-sensitive.
                        try:
                            script_parser.read_string(script_str)
                        except configparser.Error as e:
                            Logger.error("Stored post-processing scripts have syntax errors: {err}".format(err = str(e)))
                            continue
                        for script_name, settings in script_parser.items():  # There should only be one, really! Otherwise we can't guarantee the order or allow multiple uses of the same script.
                            if script_name == "DEFAULT":  # ConfigParser always has a DEFAULT section, but we don't fill it. Ignore this one.
                                continue
                            setting_param = ""
                            for setting_key, setting_value in settings.items():
                                setting_param += setting_key + " : " + setting_value + "<br>"
                            self._WriteTdNormal(stream,script_name,setting_param)
                            
        stream.write("</table>")
        stream.write("</body>")
        stream.write("</html>")
        return True

    def _WriteTdNormal(self,stream,Key,ValStr):

        stream.write("<tr class='normal'>")
        stream.write("<td class='w-50'>" + Key + "</td>")
        stream.write("<td colspan='2'>" + str(ValStr) + "</td>")
        stream.write("</tr>\n")
        
    def _WriteTd(self,stream,Key,ValStr):

        stream.write("<tr>")
        stream.write("<td class='w-50'>" + Key + "</td>")
        stream.write("<td colspan='2'>" + str(ValStr) + "</td>")
        stream.write("</tr>\n")
            
               
    def _doTree(self,stack,key,stream,depth,extrud):   
        #output node
        Info_Extrud=""
        definition_key=key + " label"
        ExtruderStrg = catalog.i18nc("@label", "Extruder")
        top_of_stack = cast(InstanceContainer, stack.getTop())  # Cache for efficiency.
        changed_setting_keys = top_of_stack.getAllKeys()            

        if stack.getProperty(key,"type") == "category":
            stream.write("<tr class='category'>")
            if extrud>0:
                untranslated_label=stack.getProperty(key,"label")
                translated_label=i18n_catalog.i18nc(definition_key, untranslated_label) 
                Pos = int(stack.getMetaDataEntry("position"))   
                Pos += 1
                Info_Extrud="%s : %d %s"%(ExtruderStrg,Pos,translated_label)
            else:
                untranslated_label=stack.getProperty(key,"label")
                translated_label=i18n_catalog.i18nc(definition_key, untranslated_label)
                Info_Extrud=str(translated_label)
            stream.write("<td colspan='3'>" + str(Info_Extrud) + "</td>")
            #stream.write("<td class=category>" + str(key) + "</td>")
            stream.write("</tr>\n")
        else:
            if stack.getProperty(key,"enabled") == False:
                stream.write("<tr class='disabled'>")
            else:
                if key in self._modified_global_param or key in changed_setting_keys : # changed_setting_keys:
                    stream.write("<tr class='local'>")
                else:
                    stream.write("<tr class='normal'>")
            
            # untranslated_label=stack.getProperty(key,"label").capitalize()
            untranslated_label=stack.getProperty(key,"label")           
            translated_label=i18n_catalog.i18nc(definition_key, untranslated_label)

            if translated_label == untranslated_label and self.cura_locale != "en_US" :
                # Logger.log("d", "translated/unstranslated = %s ; %s",translated_label, untranslated_label)
                stream.write("<td class='w-70o pl-"+str(depth)+"'>" + str(translated_label) + "</td>")
            else :
                stream.write("<td class='w-70 pl-"+str(depth)+"'>" + str(translated_label) + "</td>")            

            GetType=stack.getProperty(key,"type")
            GetVal=stack.getProperty(key,"value")
            
            if str(GetType)=='float':
                # GelValStr="{:.2f}".format(GetVal).replace(".00", "")  # Formatage
                GelValStr="{:.4f}".format(GetVal).rstrip("0").rstrip(".") # Formatage thanks to r_moeller
            else:
                # enum = Option list
                if str(GetType)=='enum':
                    definition_option=key + " option " + str(GetVal)
                    get_option=str(GetVal)
                    GetOption=stack.getProperty(key,"options")
                    GetOptionDetail=GetOption[get_option]
                    GelValStr=i18n_catalog.i18nc(definition_option, GetOptionDetail)
                    # Logger.log("d", "GetType_doTree = %s ; %s ; %s ; %s",definition_option, GelValStr, GetOption, GetOptionDetail)
                else:
                    GelValStr=str(GetVal).replace(r"\n", "<br>")
            
            stream.write("<td class='val'>" + GelValStr + "</td>")
            
            stream.write("<td class='w-10'>" + str(stack.getProperty(key,"unit")) + "</td>")
            stream.write("</tr>\n")

            depth += 1

        #look for children
        if len(CuraApplication.getInstance().getGlobalContainerStack().getSettingDefinition(key).children) > 0:
            for i in CuraApplication.getInstance().getGlobalContainerStack().getSettingDefinition(key).children:       
                self._doTree(stack,i.key,stream,depth,extrud)                
    
    def _doTreeExtrud(self,stack,key,stream,depth,extrud):   
        #output node
        Info_Extrud=""
        definition_key=key + " label"
        ExtruderStrg = catalog.i18nc("@label", "Extruder")
        top_of_stack = cast(InstanceContainer, stack.getTop())  # Cache for efficiency.
        changed_setting_keys = top_of_stack.getAllKeys()
        
        if stack.getProperty(key,"type") == "category":
            if extrud>0:
                untranslated_label=stack.getProperty(key,"label")
                translated_label=i18n_extrud_catalog.i18nc(definition_key, untranslated_label)
                Pos = int(stack.getMetaDataEntry("position"))   
                Pos += 1                
                Info_Extrud="%s : %d %s"%(ExtruderStrg,Pos,translated_label)
            else:
                untranslated_label=stack.getProperty(key,"label")
                translated_label=i18n_extrud_catalog.i18nc(definition_key, untranslated_label)
                Info_Extrud=str(translated_label)
            stream.write("<tr class='category'><td colspan='3'>" + str(Info_Extrud) + "</td>")
            stream.write("</tr>\n")
        else:
            if stack.getProperty(key,"enabled") == False:
                stream.write("<tr class='disabled'>")
            else:
                if key in self._modified_global_param or key in changed_setting_keys : #changed_setting_keys:
                    stream.write("<tr class='local'>")
                else:
                    stream.write("<tr class='normal'>")
            
            # untranslated_label=stack.getProperty(key,"label").capitalize()
            untranslated_label=stack.getProperty(key,"label")           
            translated_label=i18n_extrud_catalog.i18nc(definition_key, untranslated_label)
            
            if translated_label == untranslated_label and self.cura_locale != "en_US" :
                # Logger.log("d", "translated/unstranslated = %s ; %s",translated_label, untranslated_label)
                stream.write("<td class='w-70o pl-"+str(depth)+"'>" + str(translated_label) + "</td>")
            else :
                stream.write("<td class='w-70 pl-"+str(depth)+"'>" + str(translated_label) + "</td>")
            
            GetType=stack.getProperty(key,"type")
            GetVal=stack.getProperty(key,"value")
            if str(GetType)=='float':
                # GelValStr="{:.2f}".format(GetVal).replace(".00", "")  # Formatage
                GelValStr="{:.4f}".format(GetVal).rstrip("0").rstrip(".") # Formatage thanks to r_moeller
            else:
                # enum = Option list
                if str(GetType)=='enum':
                    definition_option=key + " option " + str(GetVal)
                    get_option=str(GetVal)
                    GetOption=stack.getProperty(key,"options")
                    GetOptionDetail=GetOption[get_option]
                    GelValStr=i18n_catalog.i18nc(definition_option, GetOptionDetail)
                    # Logger.log("d", "GetType_doTree = %s ; %s ; %s ; %s",definition_option, GelValStr, GetOption, GetOptionDetail)
                else:
                    GelValStr=str(GetVal).replace(r"\n", "<br>")
                
            stream.write("<td class='val'>" + GelValStr + "</td>")
            
            stream.write("<td class='w-10'>" + str(stack.getProperty(key,"unit")) + "</td>")
            stream.write("</tr>\n")

            depth += 1

        #look for children
        if len(stack.getSettingDefinition(key).children) > 0:
            for i in stack.getSettingDefinition(key).children:       
                self._doTreeExtrud(stack,i.key,stream,depth,extrud)
    # Compatibility Cura 4.10 and upper
    @call_on_qt_thread  # must be called from the main thread because of OpenGL
    def _createSnapshot(self):
        Logger.log("d", "Creating thumbnail image...")
        if not CuraApplication.getInstance().isVisible:
            Logger.log("w", "Can't create snapshot when renderer not initialized.")
            return None
        try:
            snapshot = Snapshot.snapshot(width = 300, height = 300)
        except:
            Logger.logException("w", "Failed to create snapshot image")
            return None

        return snapshot
