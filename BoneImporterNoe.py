from inc_noesis import *

#registerNoesisTypes is called by Noesis to allow the script to register formats.
#Do not implement this function in script files unless you want them to be dedicated format modules!
def registerNoesisTypes():
	handle = noesis.register("Noesis Python Cod Skeleton", ".skel")
	#noesis.setHandlerTypeCheck(handle, noepyCheckType)

	noesis.setHandlerLoadModel(handle, LoadModel)

	#noesis.setHandlerWriteModel(handle, noepyWriteModel)

	#noesis.setHandlerWriteAnim(handle, noepyWriteAnim)
	#any noesis.NMSHAREDFL_* flags can be applied here, to affect the model which is handed off to the exporter.
	#adding noesis.NMSHAREDFL_FLATWEIGHTS_FORCE4 would force us to 4 weights per vert.
	#noesis.setTypeSharedModelFlags(handle, noesis.NMSHAREDFL_FLATWEIGHTS)

	noesis.logPopup()
	print("The log can be useful for catching debug prints from preview loads.\nBut don't leave it on when you release your script, or it will probably annoy people.")
	return 1

    
def LoadModel(data, mdlList):
	print("get here?")
	bs = NoeBitStream(data)
	bones = []
	numBones = 65
	#bs.readInt()
	for i in range(0, numBones):
		bone = CodVitaReadBone(bs)
		bones.append(bone)
	print(bones)
    
    
    
    
#write bone
def noepyWriteBone(bs, bone):
	bs.writeInt(bone.index)
	bs.writeString(bone.name)
	bs.writeString(bone.parentName)
	bs.writeInt(bone.parentIndex)
	bs.writeBytes(bone.getMatrix().toBytes())

#read bone
def CodVitaReadBone(bs):
	#boneIndex = bs.readInt()
	#boneName = bs.readString()
	#bonePName = bs.readString()
	boneMat = NoeMat44.fromBytes(bs.readBytes(64))
	bs.seek(0x20)
	bonePIndex = bs.readInt()
	bs.seek(0xC)
	
	return NoeBone(boneMat, bonePIndex)