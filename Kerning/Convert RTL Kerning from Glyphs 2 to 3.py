#MenuTitle: Convert RTL Kerning from Glyphs 2 to 3
from __future__ import division, print_function, unicode_literals
__doc__="""
Convert RTL kerning from Glyphs 2 to Glyphs 3 format and switches the kerning classes. Detailed report in Macro Window.

Hold down OPTION and SHIFT to convert from Glyphs 3 back to Glyphs 2.
"""

from GlyphsApp import objcObject, RTL
from AppKit import NSEvent
from Foundation import NSMutableDictionary

def nameForKey(thisKey):
	if thisKey.startswith("@"):
		return thisKey
	else:
		return thisFont.glyphForId_(thisKey).name

def glyphNameIsRTL(glyphName, key2Scripts):
	glyphName = glyphName.replace("@","")
	if glyphName in key2Scripts.keys():
		if GSGlyphsInfo.isRTLScript_(key2Scripts[glyphName]):
			return True
	return False

def stripMMK(name):
	return name.replace("MMK_L_","").replace("MMK_R_","")

def copyFrom3to2(thisFont, masterKerning, RTLmasterKerning, key2Scripts):
	countKernPairs = 0
	for firstKey in list(RTLmasterKerning.allKeys()):
		firstKerning = RTLmasterKerning[firstKey]
		newFirstKerning = {}
		
		firstName = nameForKey(firstKey)
		if glyphNameIsRTL(firstName, key2Scripts):
			newFirstKey = firstKey.replace("@MMK_R_", "@MMK_L_")

		for secondKey in firstKerning.keys():
			secondName = nameForKey(secondKey)
			if glyphNameIsRTL(secondName, key2Scripts):
				newSecondKey = secondKey.replace("@MMK_L_", "@MMK_R_")
				
			kernValue = firstKerning[secondKey]
			thisFont.setKerningForPair(master.id, stripMMK(firstName), stripMMK(secondName), kernValue)
			print("  ✅ %s %s %i" % (
				stripMMK(firstName),
				stripMMK(secondName),
				kernValue,
			))
			countKernPairs += 1
	
		del(RTLmasterKerning[firstKey])

	return countKernPairs

def copyFrom2to3(masterKerning, RTLmasterKerning, key2Scripts):
	countKernPairs = 0
	for firstKey in list(masterKerning.allKeys()):
		firstKeyIsRTL = False
		
		# check if first key is RTL
		firstName = nameForKey(firstKey)
		if glyphNameIsRTL(firstName, key2Scripts):
			firstKeyIsRTL = True
			
		firstKerning = masterKerning[firstKey]
		newFirstKey = firstKey.replace("@MMK_L_", "@MMK_R_")
		newFirstKerning = {}
		
		for secondKey in firstKerning.allKeys():
			secondKeyIsRTL = False
			
			# check if second key is RTL
			if not firstKeyIsRTL:
				secondName = nameForKey(secondKey)
				if glyphNameIsRTL(secondName, key2Scripts):
					secondKeyIsRTL = True
			
			# if either is RTL, convert to RTL kerning:
			if firstKeyIsRTL or secondKeyIsRTL:
				if not newFirstKey in RTLmasterKerning.allKeys():
					RTLmasterKerning[newFirstKey] = newFirstKerning
				newSecondKey = secondKey.replace("@MMK_R_", "@MMK_L_")
				kernValue = firstKerning[secondKey]
				newFirstKerning[newSecondKey] = kernValue
				print("  ✅ %s %s %i" % (
					nameForKey(newFirstKey).replace("MMK_R_",""),
					nameForKey(newSecondKey).replace("MMK_L_",""),
					kernValue,
				))
				countKernPairs += 1
				del(masterKerning[firstKey][secondKey])
		
		if not masterKerning[firstKey] is None and not masterKerning[firstKey]:
			del(masterKerning[firstKey])
			
	return countKernPairs

def mapGlyphsToScripts(thisFont):
	ExportClass = NSClassFromString("GSExportInstanceOperation")
	exporter = ExportClass.new()
	exporter.setFont_(thisFont)
	glyph2script = {}
	exporter._makeKey2Scripts_splitGroups_GroupDict_error_(glyph2script, None, {}, None)
	return glyph2script


# see which keys are pressed:
keysPressed = NSEvent.modifierFlags()
optionKey, shiftKey = 524288, 131072
optionKeyPressed = keysPressed & optionKey == optionKey
shiftKeyPressed = keysPressed & shiftKey == shiftKey
userWantsToConvertFrom3to2 = optionKeyPressed and shiftKeyPressed

# map glyphs to scripts for the current font:
thisFont = Glyphs.font
glyph2scriptMapping = mapGlyphsToScripts(thisFont)

# prepare Macro Window logging:
Glyphs.clearLog()
conversionDirection = "%i → %i:" % (
	3 if userWantsToConvertFrom3to2 else 2,
	2 if userWantsToConvertFrom3to2 else 3,
)

# copy RTL kerning and swith class prefixes in kern dict
print("1️⃣ Convert RTL kerning from Glyphs %s" % conversionDirection)
countKernPairs = 0
for master in thisFont.masters:
	print("\n  🔠 Master: %s" % master.name)
	RTLMasterKerning = thisFont.kerningRTL.get(master.id, None)
	if RTLMasterKerning is None:
		RTLMasterKerning = NSMutableDictionary.new()
		thisFont.kerningRTL[master.id] = RTLMasterKerning
	
	masterKerning = thisFont.kerning.get(master.id, None)
	if userWantsToConvertFrom3to2:
		countKernPairs = copyFrom3to2(thisFont, masterKerning, RTLMasterKerning, glyph2scriptMapping)
	else:
		if not masterKerning:
			print("  No kerning found in this master.")
			continue
		countKernPairs = copyFrom2to3(masterKerning, RTLMasterKerning, glyph2scriptMapping)

# Switch kerning groups in glyphs:
print("\n2️⃣ Flipping kerning groups for RTL glyphs:")
countFlippedGroups = 0
for g in thisFont.glyphs:
	if g.direction == RTL and (g.rightKerningGroup or g.leftKerningGroup) and g.rightKerningGroup != g.leftKerningGroup:
		countFlippedGroups += 1
		rightGroup = g.rightKerningGroup
		leftGroup = g.leftKerningGroup
		g.rightKerningGroup = leftGroup
		g.leftKerningGroup = rightGroup
		print("  ↔️ %s   ◀️ %s  ▶️ %s" % (
			g.name,
			g.leftKerningGroup,
			g.rightKerningGroup,
		))

print("\n✅ Done.")
# Floating notification:
Glyphs.showNotification( 
	"RTL kerning %s for %s" % (conversionDirection, thisFont.familyName),
	"Converted %i pair%s, flipped groups in %i glyph%s. Details in Macro Window." % (
		countKernPairs,
		"" if countKernPairs==1 else "s",
		countFlippedGroups,
		"" if countFlippedGroups==1 else "s",
	),
	)

