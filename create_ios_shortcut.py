"""
Generate iOS Shortcut for posting golf rounds to WhatsApp
Run this script to create a .shortcut file that you can AirDrop to your iPhone
"""
import plistlib
import base64

# Define the shortcut actions
shortcut = {
    "WFWorkflowActions": [
        # Step 1: Get URLs from Input (extract URL from text)
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.detect.link",
            "WFWorkflowActionParameters": {
                "WFInput": {
                    "Value": {
                        "string": "￼",
                        "attachmentsByRange": {
                            "{0, 1}": {
                                "Type": "Variable",
                                "VariableName": "Shortcut Input"
                            }
                        }
                    }
                }
            }
        },
        # Step 2: Dictionary
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.dictionary",
            "WFWorkflowActionParameters": {
                "WFItems": {
                    "Value": {
                        "WFDictionaryFieldValueItems": [
                            {
                                "WFItemType": 0,
                                "WFKey": {"Value": {"string": "action", "attachmentsByRange": {}}},
                                "WFValue": {"Value": {"string": "add_round", "attachmentsByRange": {}}}
                            },
                            {
                                "WFItemType": 0,
                                "WFKey": {"Value": {"string": "url", "attachmentsByRange": {}}},
                                "WFValue": {
                                    "Value": {
                                        "string": "￼",
                                        "attachmentsByRange": {
                                            "{0, 1}": {
                                                "OutputUUID": "00000000-0000-0000-0000-000000000001",
                                                "Type": "ActionOutput",
                                                "OutputName": "URLs"
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        },
        # Step 3: Get Contents of URL
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
            "WFWorkflowActionParameters": {
                "WFHTTPMethod": "POST",
                "WFHTTPHeaders": {
                    "Value": {
                        "WFDictionaryFieldValueItems": [
                            {
                                "WFItemType": 0,
                                "WFKey": {"Value": {"string": "Content-Type", "attachmentsByRange": {}}},
                                "WFValue": {"Value": {"string": "application/json", "attachmentsByRange": {}}}
                            },
                            {
                                "WFItemType": 0,
                                "WFKey": {"Value": {"string": "X-Auth-Token", "attachmentsByRange": {}}},
                                "WFValue": {"Value": {"string": "HnB9_VsxLXQVVQqNXi2ilSyY0hPQDJ9EcEt-mVoGej0", "attachmentsByRange": {}}}
                            }
                        ]
                    }
                },
                "WFHTTPBodyType": "JSON",
                "WFJSONValues": {
                    "Value": {
                        "string": "￼",
                        "attachmentsByRange": {
                            "{0, 1}": {
                                "OutputUUID": "00000000-0000-0000-0000-000000000002",
                                "Type": "ActionOutput",
                                "OutputName": "Dictionary"
                            }
                        }
                    }
                },
                "WFURL": "https://wgrf7ptkhss36vmv7zph4aqzxy0spsff.lambda-url.ap-southeast-2.on.aws/"
            }
        },
        # Step 4: Get Dictionary from Input
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.getdictionaryfromcontentsobject",
            "WFWorkflowActionParameters": {}
        },
        # Step 5: Get Value for Key
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
            "WFWorkflowActionParameters": {
                "WFDictionaryKey": "summary"
            }
        },
        # Step 6: Send Message via WhatsApp
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.sendmessage",
            "WFWorkflowActionParameters": {
                "WFSendMessageActionApp": "WhatsApp"
            }
        }
    ],
    "WFWorkflowClientVersion": "2302.0.4",
    "WFWorkflowClientRelease": "2.2",
    "WFWorkflowMinimumClientVersion": 900,
    "WFWorkflowMinimumClientRelease": "2.0",
    "WFWorkflowIcon": {
        "WFWorkflowIconStartColor": 2071128575,
        "WFWorkflowIconGlyphNumber": 59511
    },
    "WFWorkflowTypes": ["NCWidget", "WatchKit"],
    "WFWorkflowInputContentItemClasses": [
        "WFAppStoreAppContentItem",
        "WFArticleContentItem",
        "WFContactContentItem",
        "WFDateContentItem",
        "WFEmailAddressContentItem",
        "WFGenericFileContentItem",
        "WFImageContentItem",
        "WFiTunesProductContentItem",
        "WFLocationContentItem",
        "WFDCMapsLinkContentItem",
        "WFAVAssetContentItem",
        "WFPDFContentItem",
        "WFPhoneNumberContentItem",
        "WFRichTextContentItem",
        "WFSafariWebPageContentItem",
        "WFStringContentItem",
        "WFURLContentItem"
    ],
    "WFWorkflowImportQuestions": [],
    "WFWorkflowName": "Post Golf Round"
}

# Add UUIDs to actions for reference
shortcut["WFWorkflowActions"][0]["UUID"] = "00000000-0000-0000-0000-000000000001"  # Get URLs
shortcut["WFWorkflowActions"][1]["UUID"] = "00000000-0000-0000-0000-000000000002"  # Dictionary

# Write the shortcut file
output_file = "Post_Golf_Round.shortcut"
with open(output_file, 'wb') as f:
    plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)

print(f"✅ iOS Shortcut created: {output_file}")
print(f"\nNext steps:")
print(f"1. AirDrop '{output_file}' to your iPhone")
print(f"2. Tap the file on your iPhone")
print(f"3. Tap 'Add Shortcut' to import it")
print(f"4. Go to Shortcuts app → tap ... on the shortcut → Settings → Enable 'Show in Share Sheet' → Select 'URLs' and 'Safari web pages'")
print(f"5. Test it by opening a Tag Heuer scorecard in Safari and using Share → Post Golf Round")
