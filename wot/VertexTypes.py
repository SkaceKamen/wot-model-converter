''' Vertex Types '''



#####################################################################
# vt_baseType

class vt_baseType(object):
	uv2 = None
	FORMAT = ''
	SIZE = 0
	IS_SKINNED = False
	IS_NEW = False
	V_TYPE = ''



#####################################################################
# vt_SET3_XYZNUVTB

class vt_SET3_XYZNUVTBPC(vt_baseType):
	FORMAT = '<3fI2f2I'
	SIZE = 32
	IS_SKINNED = False
	IS_NEW = True
	V_TYPE = 'set3/xyznuvtbpc'



#####################################################################
# vt_SET3_XYZNUVPC

class vt_SET3_XYZNUVPC(vt_baseType):
	FORMAT = '<3fI2f'
	SIZE = 24
	IS_SKINNED = False
	IS_NEW = True
	V_TYPE = 'set3/xyznuvpc'



#####################################################################
# vt_SET3_XYZNUVIIIWWTBPC

class vt_SET3_XYZNUVIIIWWTBPC(vt_baseType):
	FORMAT = '<3fI2f8B2I'
	SIZE = 40
	IS_SKINNED = True
	IS_NEW = True
	V_TYPE = 'set3/xyznuviiiwwtbpc'



#####################################################################
# vt_XYZNUVIIIWWTB

class vt_XYZNUVIIIWWTB(vt_baseType):
	FORMAT = '<3fI2f5B2I'
	SIZE = 37
	IS_SKINNED = True
	IS_NEW = False
	V_TYPE = 'xyznuviiiwwtb'



#####################################################################
# vt_XYZNUVTB

class vt_XYZNUVTB(vt_baseType):
	FORMAT = '<3fI2f2I'
	SIZE = 32
	IS_SKINNED = False
	IS_NEW = False
	V_TYPE = 'xyznuvtb'



#####################################################################
# vt_XYZNUV

class vt_XYZNUV(vt_baseType):
	FORMAT = '<3fI2f'
	SIZE = 24
	IS_SKINNED = False
	IS_NEW = False
	V_TYPE = 'xyznuv'
