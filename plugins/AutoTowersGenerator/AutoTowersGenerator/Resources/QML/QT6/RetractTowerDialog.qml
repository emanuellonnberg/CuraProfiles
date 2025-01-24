import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

import UM 1.6 as UM
import Cura 1.7 as Cura

UM.Dialog
{
    id: dialog

	property variant catalog: UM.I18nCatalog { name: "autotowers" }
	
    title: catalog.i18nc("@title", "Retraction Tower")

    buttonSpacing: UM.Theme.getSize('default_margin').width
    minimumWidth: screenScaleFactor * 445
    minimumHeight: (screenScaleFactor * contents.childrenRect.height) + (2 * UM.Theme.getSize('default_margin').height) + UM.Theme.getSize('button').height
    maximumHeight: minimumHeight
    width: minimumWidth
    height: minimumHeight

    backgroundColor: UM.Theme.getColor('main_background')

    // Define the width of the number input text boxes
    property int numberInputWidth: UM.Theme.getSize('button').width



    RowLayout
    {
        id: contents
        width: dialog.width - 2 * UM.Theme.getSize('default_margin').width
        spacing: UM.Theme.getSize('default_margin').width

        // Display the icon for this tower
        Rectangle
        {
            Layout.preferredWidth: icon.width
            Layout.preferredHeight: icon.height
            Layout.fillHeight: true
            color: UM.Theme.getColor('primary_button')

            Image
            {
                id: icon
                source: Qt.resolvedUrl('../../Images/' + dataModel.dialogIcon)
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }

        GridLayout
        {
            columns: 2
            rowSpacing: UM.Theme.getSize('default_lining').height
            columnSpacing: UM.Theme.getSize('default_margin').width
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignTop
 
            // Preset option
            UM.Label
            {
                text: catalog.i18nc("@label", "Retract Tower Preset")
                MouseArea
                {
                    id: preset_mouse_area
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }
            Cura.ComboBox
            {
                Layout.fillWidth: true
                model: enableCustom ? dataModel.presetsModel.concat({'name': catalog.i18nc("@model", "Custom")}) : dataModel.presetsModel
                textRole: 'name'
                currentIndex: dataModel.presetIndex

                onCurrentIndexChanged:
                {
                    dataModel.presetIndex = currentIndex
                }
            }

            // Tower type
            UM.Label
            {
                text: catalog.i18nc("@label", "Tower Type")
                visible: !dataModel.presetSelected
                MouseArea 
                {
                    id: tower_type_mouse_area
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }
            Cura.ComboBox
            {
                id: tower_type_selection
                Layout.fillWidth: true
                model: dataModel.towerTypesModel
                textRole: 'name'
                visible: !dataModel.presetSelected
                currentIndex: dataModel.towerTypeIndex

                onCurrentIndexChanged: 
                {
                    dataModel.towerTypeIndex = currentIndex
                }
            }
            UM.ToolTip
            {
                text: catalog.i18nc("@tooltip", "The retraction chracteristic to change over the tower.<p>\'Distance\' changes the length of filament that is retracted or extruded.<p>\'Speed\' changes how quickly the filament is retracted or extruded.")
                visible: tower_type_mouse_area.containsMouse
            }

            // Starting value
            UM.Label 
            { 
                text: catalog.i18nc("@label","Starting ") +  catalog.i18nc("@type",tower_type_selection.currentText) 
                visible: !dataModel.presetSelected
                MouseArea 
                {
                    id: starting_value_mouse_area
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }
            Cura.TextField
            {
                Layout.preferredWidth: numberInputWidth
                validator: RegularExpressionValidator { regularExpression: /[0-9]*(\.[0-9]+)?/ }
                text: dataModel.startValueStr
                visible: !dataModel.presetSelected

                onTextChanged: 
                {
                    if (dataModel.startValueStr != text) dataModel.startValueStr = text
                }
            }
            UM.ToolTip
            {
                text: catalog.i18nc("@tooltip","The retraction value (speed or distance) for the first section of the tower.<p>For \'Distance\' towers, this is the length of filament retracted or extruded for each section.<p>For \'Speed\' towers, this is the speed at which the filament is retracted or extruded.")
                visible: starting_value_mouse_area.containsMouse
            }

            // Ending value
            UM.Label 
            { 
                text: catalog.i18nc("@label","Ending ") + catalog.i18nc("@type",tower_type_selection.currentText)
                visible: !dataModel.presetSelected
                MouseArea 
                {
                    id: ending_value_mouse_area
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }
            Cura.TextField
            {
                Layout.preferredWidth: numberInputWidth
                validator: RegularExpressionValidator { regularExpression: /[0-9]*(\.[0-9]+)?/ }
                text: dataModel.endValueStr
                visible: !dataModel.presetSelected

                onTextChanged:
                {
                    if (dataModel.endValueStr != text) dataModel.endValueStr = text
                }
            }
            UM.ToolTip
            {
                text: catalog.i18nc("@tooltip","The retraction value (speed or distance) for the last section of the tower.<p>For \'Distance\' towers, this is the length of filament retracted or extruded for each section.<p>For \'Speed\' towers, this is the speed at which the filament is retracted or extruded.")
                visible: ending_value_mouse_area.containsMouse
            }

            // Value change
            UM.Label 
            { 
                text: catalog.i18nc("@type",tower_type_selection.currentText) + catalog.i18nc("@label"," Change")
                visible: !dataModel.presetSelected
                MouseArea 
                {
                    id: value_change_mouse_area
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }
            Cura.TextField
            {
                Layout.preferredWidth: numberInputWidth
                validator: RegularExpressionValidator { regularExpression: /[+-]?[0-9]*(\.[0-9]+)?/ }
                text: dataModel.valueChangeStr
                visible: !dataModel.presetSelected

                onTextChanged: 
                {
                    if (dataModel.valueChangeStr != text) dataModel.valueChangeStr = text
                }
            }
            UM.ToolTip
            {
                text: catalog.i18nc("@tooltip","The amount to change the retraction value (speed or distance) between tower sections.<p>In combination with the starting and ending values, this determines the number of sections in the tower.")
                visible: value_change_mouse_area.containsMouse
            }

            // Tower label
            UM.Label
            {
                text: catalog.i18nc("@label","Tower Label")
                visible: !dataModel.presetSelected
            }
            Cura.TextField
            {
                Layout.fillWidth: true
                text: dataModel.towerLabel
                visible: !dataModel.presetSelected

                onTextChanged: 
                {
                    if (dataModel.towerLabel != text) dataModel.towerLabel = text
                }
            }

            // Tower description
            UM.Label 
            { 
                text: catalog.i18nc("@label","Tower Description")
                visible: !dataModel.presetSelected
                MouseArea 
                {
                    id: tower_description_mouse_area
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }
            Cura.TextField
            {
                Layout.fillWidth: true
                text: dataModel.towerDescription
                visible: !dataModel.presetSelected

                onTextChanged: 
                {
                    if (dataModel.towerDescription != text) dataModel.towerDescription = text
                }
            }
            UM.ToolTip
            {
                text: catalog.i18nc("@label","An optional label to carve up the left side of the tower.<p>This can be used, for example, to identify the purpose of the tower or the material being printed.")
                visible: tower_description_mouse_area.containsMouse
            }
        }
    }

    rightButtons: 
    [
        Cura.SecondaryButton
        {
            text: catalog.i18nc("@button","Cancel")
            onClicked: dialog.reject()
        },
        Cura.PrimaryButton
        {
            text: catalog.i18nc("@button","OK")
            onClicked: dialog.accept()
        }
    ]

    onAccepted:
    {
        controller.dialogAccepted()
    }

}
