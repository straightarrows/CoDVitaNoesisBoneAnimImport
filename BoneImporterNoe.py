from calendar import c
#from mathutils import *
import re
from this import d #regex
import time
import os # for path stuff
import ntpath
import math 
from inc_noesis import *


#registerNoesisTypes is called by Noesis to allow the script to register formats.
#Do not implement this function in script files unless you want them to be dedicated format modules!
def registerNoesisTypes():
	handle = noesis.register("Noesis Python Cod Skeleton", ".comb")
	noesis.setHandlerTypeCheck(handle, GenericCheckType)

	noesis.setHandlerLoadModel(handle, LoadModel)

	#handle = noesis.register("Noesis Cod Vita Anim!", ".saf") do this later when script more set up
	#noesis.setHandlerTypeCheck(handle, GenericCheckType)
	
	#noesis.setHandlerWriteAnim(handle, noepyWriteAnim)
	#any noesis.NMSHAREDFL_* flags can be applied here, to affect the model which is handed off to the exporter.
	#adding noesis.NMSHAREDFL_FLATWEIGHTS_FORCE4 would force us to 4 weights per vert.
	#noesis.setTypeSharedModelFlags(handle, noesis.NMSHAREDFL_FLATWEIGHTS)

	noesis.logPopup()
	print("The log can be useful for catching debug prints from preview loads.\nBut don't leave it on when you release your script, or it will probably annoy people.")
	return 1

def GenericCheckType(data): #this is required for noesis
	if len(data) < 8:
		return 0
	return 1

def ReadFloatQuaternions(bs):
	W = bs.readFloat()
	X = bs.readFloat()
	Y = bs.readFloat()
	Z = bs.readFloat()
	return NoeQuat((X,Y,Z,W))

def ReadandNormalizeShortQuaternions(bs):
	W = bs.readShort()/32768
	X = bs.readShort()/32768
	Y = bs.readShort()/32768
	Z = bs.readShort()/32768
	#normalize it - this doesnt fix anything
	sum = W*W + X*X + Y*Y + Z*Z
	

	NormFactor = math.sqrt(sum)
	print("W is", W)
	if W == -1.0:
		W = 1.0
   
	return NoeQuat((X/NormFactor,Y/NormFactor,Z/NormFactor,W/NormFactor))

def ReadTranslations(bs):
	X = bs.readFloat()
	Y= bs.readFloat()
	Z= bs.readFloat()
	return NoeVec3((X,Y,Z))
	
def QuaternionMul(quat1, quat2): #this is giving wxyz dont use till fixed
	w0, x0, y0, z0 = quat1
	w1, x1, y1, z1 = quat2
	return NoeQuat([-x1 * x0 - y1 * y0 - z1 * z0 + w1 * w0,
                     x1 * w0 + y1 * z0 - z1 * y0 + w1 * x0,
                     -x1 * z0 + y1 * w0 + z1 * x0 + w1 * y0,
                     x1 * y0 - y1 * x0 + z1 * w0 + w1 * z0])

	
def GetPoseBoneRotations(numBones,bs):
	RotList = []
	for i in range(0,numBones):
		seekvalue = i *112 #this is different between ai and fps!
		bs.seek(80+seekvalue,0)
		RotList.append(ReadFloatQuaternions(bs)) #Now have ALL the local space Quaternions in a list
	#print("theveclist", VecList)
	return RotList



def LoadQuaternionsIntoNoe(BoneIdxandKeyFrameChunkDic, LocalQuatsPoseArray, bs):
	NumFrames = 100 #change this on per anim basis
	KfBones = []
	#going to 
	for i in BoneIdxandKeyFrameChunkDic: #so, here we want to go through every bone 0-66, and get  pose bone if no animbone specified
		CurrentBone = i #should equal the first member of key value in dict
		print("Current bone is", CurrentBone)
		KfBone = NoeKeyFramedBone(CurrentBone)
		### This gets local transformations for current bones
		seekvalue = CurrentBone *112
		bs.seek(64+seekvalue,0)
		CurrentVector = ReadTranslations(bs)

		###
		bs.seek(9860, 0) #seek to anim section
		
		#print(BoneIdxandKeyFrameChunkDic.get(CurrentBone))
		bs.seek(BoneIdxandKeyFrameChunkDic.get(CurrentBone),1) #chang3 this
		RotationKeys = []
		
		for j in range(0, NumFrames):
			CurrentRotKey = ReadandNormalizeShortQuaternions(bs)
			print("CurrentRotKey", CurrentRotKey)
			ParentQuatToMultiply = LocalQuatsPoseArray[i]
			print("Parent Quat TO multiply by", ParentQuatToMultiply)
			#NewRotKey = QuaternionMul(ParentQuatToMultiply,CurrentRotKey)
			NewRotKey = ParentQuatToMultiply.__mul__(CurrentRotKey) #currently multipling assumed world space quat anim by local space bone quats
			#NewRotKey = LocalQuatsPoseArray[i-1].__mul__(CurrentRotKey)
			print("after multiplying here is new rotkey",NewRotKey)
			RotKeyMat = NewRotKey.toMat43()
			InverseMat = RotKeyMat.inverse()
			FinalRotKey = InverseMat.toQuat()
			KeyFramedValRot = NoeKeyFramedValue(j,FinalRotKey) #this might need to be float if we have problems
			RotationKeys.append(KeyFramedValRot)
			#print("keyframedvalue", KeyFramedValRot)
			#KeyFramedValTrans = NoeKeyFramedValue(j, CurrentVector) #this stays the same so technically could be up top but dk what the time parameter is
			#print("keyframedvalue", KeyFramedValTrans)
			#KeyFramedValScale = NoeKeyFramedValue(0.0, 1)
			#print("keyframedvalue", KeyFramedValScale)
			
			#KfBone.setTranslation(KeyFramedValTrans)
			#KfBone.setScale(KeyFramedValScale)
		KfBone.setRotation(RotationKeys)
		#print("KfBone is", KfBone)	
		KfBones.append(KfBone)
		#print("KfBones are", KfBone)
	return KfBones

			

#read anim
def ReadAnim(bs,LocalQuatsPoseArray):
	bs.seek(9860, 0) #seek to anim section 9860 for ai, 9156 for fps
	AnimBoneCount = bs.readInt() - 1 #for the anims that use helper bone 70
	bs.seek(92,1)
	BoneIdxandKeyFrameChunkDic = {}
	
	
	for i in range(0,AnimBoneCount):
		KeyFrameBone = bs.readInt()
		#BoneIdxandKeyFrameChunkDic.append(KeyFrameBone)
		bs.seek(12,1)
		ChunkLocation = bs.readInt()
		#BoneIdxandKeyFrameChunkDic.append(ChunkLocation)
		BoneIdxandKeyFrameChunkDic.update({KeyFrameBone:ChunkLocation})
		bs.seek(4,1)
	#VecList = GetPoseBoneTranslations(KeyFrameBoneList,bs)
	print(BoneIdxandKeyFrameChunkDic)
	KfBoneArray = LoadQuaternionsIntoNoe(BoneIdxandKeyFrameChunkDic,LocalQuatsPoseArray,bs)
	
	return KfBoneArray
		


#read bone
def CodVitaReadBone(bs, index):
	#boneIndex = bs.readInt()
	#boneName = bs.readString()
	#bonePName = bs.readString()
	
	boneName = "Bone_" +str(index)
	boneMat = NoeMat44.fromBytes(bs.readBytes(64)) #remember world space and still inversed
	boneMatinverse = NoeMat44.inverse(boneMat)
	boneMat33 = NoeMat44.toMat43(boneMatinverse) #should be bonematinverse
	#print(boneMat33)
	bs.seek(32,1)
	bonePIndex = bs.readInt()
	bs.seek(12,1)
	
	return NoeBone(index, boneName, boneMat33, parentName = None, parentIndex = bonePIndex)

def LoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	rapi.rpgClearBufferBinds()
	#print("get here?")
	bs = NoeBitStream(data)
	#VertBuff = bs.readBytes(10 * 0x58)
	#rapi.rpgBindPositionBufferOfs(VertBuff, noesis.RPGEODATA_FLOAT, 88, 0)
	
	#rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, 10, noesis.RPGEO_POINTS, 1)

	
	bones = []
	Anims = []
	numBones = 66 # STARTING AT BASE JOINT (0,0,0,) IS 0TH BONE. 55 is shoulder blade, 56 is the weapon thingy, 57 is hip central, etc
	#64 bones for fp, 66 bones for ai 3rd person
	bs.seek(0,0)
	for i in range(0, numBones):
		bone = CodVitaReadBone(bs,i)
		bones.append(bone)
	print(bones)
	mdl = NoeModel() 
	mdl.setBones(bones)
	LocalQuatsPoseArray = GetPoseBoneRotations(numBones,bs)
	print("local quat pose array", LocalQuatsPoseArray)
	KfBones = ReadAnim(bs,LocalQuatsPoseArray)
	#print(KfBones)
	KfAnim = NoeKeyFramedAnim("walk_cycle",bones,KfBones,1.0)
	Anims.append(KfAnim)
	
	mdl.setAnims(Anims)
	mdlList.append(mdl)	
	rapi.setPreviewOption("setAngOfs", "0 0 0")
	rapi.setPreviewOption("setAnimSpeed", "20")
	return 1