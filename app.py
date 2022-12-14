from flask import Flask,render_template,url_for,redirect,request,session
import json,os,cv2,shutil
import numpy as np
import argparse
import time

from face_detection import init_FD, inference_FD
from face_recognition import init_FR, feature_extraction, compare_feature


app=Flask(__name__)
app.secret_key= b'_5#y2L"F4Q8z]/'

@app.route('/enroll/',methods=['GET','POST'])
def enroll():
	if request.method == 'POST':
		if request.values['send'] == '確認':
			print('enroll face!')
			return redirect(url_for('album'))
	return render_template('enroll.html')

@app.route('/fr/<output>',methods=['GET','POST'])
def fr(output):
	if request.method == 'POST':
		if request.values['send'] == '確認':
			print('get into fr process!!')
			return redirect(url_for('album'))
	return render_template('fr.html', output=output)

def video_photo(video_path,out_path):

	cap = cv2.VideoCapture(video_path)
	ret, frame = cap.read()
	cap.release()
	print(ret)
	fill_photo(frame,out_path)

def fill_photo(img,out_path):

	width=150
	h,w=img.shape[0],img.shape[1]
	side=max(h,w)
	new = np.zeros((side,side,3), np.uint8)
	new.fill(255)
	if w>h:
		center=((side-h)/2.0)
		for i in range(img.shape[0]):
			for j in range(img.shape[1]):			
				new[int(i+center),j]=img[i,j]
	else:
		center=((side-w)/2.0)
		for i in range(img.shape[0]):
			for j in range(img.shape[1]):			
				new[i,int(j+center)]=img[i,j]

	ratio= width * 1.0 / side
	new=cv2.resize(new, None, fx=ratio, fy=ratio)
	cv2.imwrite(out_path, new)
	

@app.route('/',methods=['POST','GET'])
def index():
	with open('./member.json','r') as file_object:
		member = json.load(file_object)
	return render_template('index.html',user=session.get('username'),USERS=list(member.keys()))


@app.route('/register/',methods=['POST','GET'])
def register():
	with open('./member.json','r') as file_object:
		member = json.load(file_object)
	if request.method=='POST':
		if request.values['send']=='送出':
			if request.values['userid'] in member:
				for find in member:
					if member[find]['nick']==request.values['username']:
						return render_template('register.html',alert='this account and nickname are used.')
				return render_template('register.html',alert='this account is used.',nick=request.values['username'])
			else:
				for find in member:
					if member[find]['nick']==request.values['username']:
						return render_template('register.html',alert='this nickname are used.',id=request.values['userid'],pw=request.values['userpw'])
				member[request.values['userid']]={'password':request.values['userpw'],'nick':request.values['username']}
				with open('./member.json','w') as f:
					json.dump(member, f)
				basepath = os.path.join(os.path.dirname(__file__), 'static','uploads')
				os.mkdir(os.path.join(basepath,request.values['userid']))
				return render_template('index.html')
	return render_template('register.html')

@app.route('/login/',methods=['GET','POST'])
def login():

	if request.method== 'POST' :
		with open('./member.json','r') as file_object:
			member = json.load(file_object)

		if request.values['userid'] in member:
			if member[request.values['userid']]['password']==request.values['userpw']:
				session['username']=request.values['userid']
				session['width']=request.values['bodywidth']
				session['edit']=False
				
				return redirect ( url_for ( 'index' ))
			else:
				return render_template('login.html',alert="Your password is wrong, please check again!")
		else:
			return render_template('login.html',alert="Your account is unregistered.")
	return render_template('login.html')


@app.route('/logout/',methods=['GET','POST'])
def logout():
	if request.method=='POST':
		if request.values['send']=='確定':
			session.pop('username',None)
			session.pop('width',None)
			
		return redirect(url_for('index'))
	return render_template('logout.html')

@app.route('/upload/',methods=['GET','POST'])
def upload():

	basepath = os.path.join(os.path.dirname(__file__), 'static','uploads')
	dirs=os.listdir(os.path.join(basepath,session.get('username')))
	dirs.insert(0,'New Folder')
	dirs.insert(0,'Not Choose')

	if request.method == 'POST':
		flist = request.files.getlist("file[]")
		
		for f in flist:
			try:
				basepath = os.path.join(os.path.dirname(__file__), 'static','uploads')
				format=f.filename[f.filename.index('.'):]
				fileName= f.filename[:f.filename.index('.')] #time.time()
				if format in ('.jpg','.png','.jpeg','.HEIC','.jfif'):
					format='.jpg'
				else:
					format='.mp4'
					

				if request.values['folder']=='0':
					return render_template('upload.html',alert='Please choose a folder or creat a folder',dirs=dirs)

				elif request.values['folder']=='1':
					if not os.path.isdir(os.path.join(basepath,session.get('username'),request.values['foldername'])):
						os.mkdir(os.path.join(basepath,session.get('username'),request.values['foldername']))
						os.mkdir(os.path.join(basepath,session.get('username'),request.values['foldername'],'video'))
						os.mkdir(os.path.join(basepath,session.get('username'),request.values['foldername'],'photo'))
						os.mkdir(os.path.join(basepath,session.get('username'),request.values['foldername'],'album'))
						os.mkdir(os.path.join(basepath,session.get('username'),request.values['foldername'],'album','video'))
						os.mkdir(os.path.join(basepath,session.get('username'),request.values['foldername'],'album','photo'))

					if format == '.mp4':
						upload_path = os.path.join(basepath,session.get('username'),request.values['foldername'],'video',str(fileName).replace('.','')+str(format))
						album_path = os.path.join(basepath,session.get('username'),request.values['foldername'],'album','video',str(fileName).replace('.','')+'.jpg')
						
					else:
						upload_path = os.path.join(basepath,session.get('username'),request.values['foldername'],'photo',str(fileName).replace('.','')+str(format))
						album_path = os.path.join(basepath,session.get('username'),request.values['foldername'],'album','photo',str(fileName).replace('.','')+str(format))
											
				else:
					if format == '.mp4':
						upload_path = os.path.join(basepath,session.get('username'),dirs[int(request.values['folder'])],'video',str(fileName).replace('.','')+str(format))
						album_path = os.path.join(basepath,session.get('username'),dirs[int(request.values['folder'])],'album','video',str(fileName).replace('.','')+'.jpg')
					else:
						upload_path = os.path.join(basepath,session.get('username'),dirs[int(request.values['folder'])],'photo',str(fileName).replace('.','')+str(format))
						album_path = os.path.join(basepath,session.get('username'),dirs[int(request.values['folder'])],'album','photo',str(fileName).replace('.','')+str(format))
					
				f.save(upload_path)
				if format =='.mp4':
					video_photo(upload_path,album_path)
				else:
					image=cv2.imread(upload_path)
					fill_photo(image,album_path)

			except:
				return render_template('upload.html',alert='你沒有選擇要上傳的檔案',dirs=dirs)

		return redirect(url_for('upload'))
	return render_template('upload.html',dirs=dirs)


def inference_procedure(args, fd_model, fr_backbone, fr_head, image, device):
	# FD for image
	detection_time = time.time()
	ROI_img = inference_FD(fd_model, image, args)
	detection_time = time.time() - detection_time
	print("FD time:", detection_time)

	if ROI_img is None:
		return None, "face not detected"

	# cv2.imshow("ROI_img", ROI_img)
	# cv2.waitKey(1)

	# FR for image
	recognition_time = time.time()
	features = feature_extraction(fr_backbone, fr_head, ROI_img, device)
	recognition_time = time.time() - recognition_time
	print("FR time:", recognition_time)

	return features, ""


def registerFR(feature, register_id, enroll_dir):
	save_path = os.path.join(enroll_dir, register_id + ".npy")
	np.save(save_path, feature)


def identify(enroll_path_list, id_feature, args):
	best_score = -100
	best_ID = None
	for enroll_path in enroll_path_list:
		enroll_feature = np.load(os.path.join("enroll", enroll_path))
		score = compare_feature(enroll_feature, id_feature)
		if score > args.fr_threshold and score > best_score:
			best_score = score
			best_ID = enroll_path.split("/")[-1].split(".npy")[0]

	return best_score, best_ID


@app.route('/album/', methods=['POST', 'GET'])
def album():

	colspan=int(int(session.get('width'))/150)
	if colspan>7:
		colspan=7
	basepath = os.path.join(os.path.dirname(__file__), 'static','uploads')
	dirs=os.listdir(os.path.join(basepath,session.get('username')))
	dirs.insert(0,'ALL')
	dirs.insert(0,'')

	dict2={} #record all folder has what number name
	
	for dir in dirs:
		if dir == "ALL" or dir == '':
			continue
		dict2[dir]={'photo':[],'video':[]}
		path=os.path.join(basepath,session.get('username'),dir,'photo')
		for lists in os.listdir(path):
			dict2[dir]['photo'].append(lists)
		path=os.path.join(basepath,session.get('username'),dir,'video')
		for lists in os.listdir(path):
			dict2[dir]['video'].append(lists)
	if request.method == 'POST':
		if request.values['folder']!='0' and request.values['folder']!='1':
			session['now_folder']=[dirs[int(request.values['folder'])]]
			return render_template('album.html',dirs=dirs,colspan=colspan, files=dict2, \
				filefolder=[dirs[int(request.values['folder'])]],username=session.get('username'),edit=session.get('edit'))
		elif request.values['folder'] =='1':
			session['now_folder']=dirs[2:]
			return render_template('album.html',dirs=dirs, colspan=colspan,\
				filefolder=dirs[2:],files=dict2,username=session.get('username'),edit=session.get('edit'))
			
		elif request.values['edit'] == '編輯模式':
			session['edit']=True
			return render_template('album.html',dirs=dirs,colspan=colspan, \
				filefolder=session.get('now_folder'),files=dict2,username=session.get('username'),edit=session.get('edit'))
		elif request.values['edit'] == '觀賞模式':
			session['edit']=False
			print(session.get('now_folder'))
			return render_template('album.html',dirs=dirs,colspan=colspan, \
				filefolder=session.get('now_folder'),files=dict2,username=session.get('username'),edit=session.get('edit'))

		elif request.values['edit'] == '刪除':
			flist = request.form.getlist("delete_box")
			for f in flist:
				muru = f[:f.index('-')]
				name = f[f.index('-') + 1:f.index('#')]
				format = f[f.index('#') + 1:]
				if format == "video":
					os.remove(os.path.join(basepath, session.get('username'), muru, 'video', name))
					os.remove(
						os.path.join(basepath, session.get('username'), muru, 'album', 'video', name[:-4] + '.jpg'))
				else:
					image_path = os.path.join(basepath, session.get('username'), muru, 'photo', name)
					os.remove(os.path.join(basepath,session.get('username'),muru,'photo',name))
					os.remove(os.path.join(basepath,session.get('username'),muru,'album','photo',name))

			dict1 = {}
			for dir in dirs:
				if dir == "ALL" or dir == '':
					continue
				dict1[dir] = {'photo': [], 'video': []}
				path = os.path.join(basepath, session.get('username'), dir, 'photo')
				for lists in os.listdir(path):
					dict1[dir]['photo'].append(lists)

				path = os.path.join(basepath, session.get('username'), dir, 'video')
				for lists in os.listdir(path):
					dict1[dir]['video'].append(lists)
				if dict1[dir] == {'photo': [], 'video': []}:
					shutil.rmtree(os.path.join(basepath, session.get('username'), dir))
					del dict1[dir]
			dirs = os.listdir(os.path.join(basepath, session.get('username')))
			dirs.insert(0, 'ALL')
			dirs.insert(0, '')
			if session.get('now_folder') not in dirs:
				session['now_folder'] = dirs[2:]

			return render_template('album.html', dirs=dirs, colspan=colspan, username=session.get('username'), \
								   filefolder=session.get('now_folder'), files=dict1, edit=session.get('edit'))

		elif request.values['edit'] == 'FR': #'刪除':
			flist = request.form.getlist("delete_box")
			for f in flist:
				muru=f[:f.index('-')]
				name=f[f.index('-')+1:f.index('#')]
				format=f[f.index('#')+1:]
				if format == "video":
					os.remove(os.path.join(basepath,session.get('username'),muru,'video',name))
					os.remove(os.path.join(basepath,session.get('username'),muru,'album','video',name[:-4]+'.jpg'))
					return 'FR testing'
				else:
					image_path = os.path.join(basepath, session.get('username'), muru,'photo', name)
					print("selected:", image_path)
					image = cv2.imread(image_path)
					if image is None:
						return 'image not found'

					print(image.shape)
					# identify
					# FD and FR
					feature, msg = inference_procedure(args, fd_model, fr_backbone, fr_head, image, device)
					if feature is None:
						return "image:{}".format(msg)
					feature = feature.reshape(-1)
					if not os.path.isdir(args.enroll_dir):
						os.mkdir(args.enroll_dir)
					enroll_path_list = os.listdir(args.enroll_dir)
					best_score, best_ID = identify(enroll_path_list, feature, args)

					if best_ID is None:
						# register
						registerFR(feature, name[:-4], args.enroll_dir)
						# return "register:{}".format(name[:-4])
						return redirect(url_for('enroll'))
					else:
						print("best score:", best_score)
						# return "identity:{} confidence:{}".format(best_ID, best_score)
						# return "identity:{}".format(best_ID)
						temp = "Best ID=" + str(best_ID)+" ; Best Score=" + str(best_score)
						return redirect(url_for('fr', output=temp))

			dict1={}
			for dir in dirs:
				if dir == "ALL" or dir == '':
					continue
				dict1[dir]={'photo':[],'video':[]}
				path=os.path.join(basepath,session.get('username'),dir,'photo')
				for lists in os.listdir(path):
					dict1[dir]['photo'].append(lists)
				
				path=os.path.join(basepath,session.get('username'),dir,'video')
				for lists in os.listdir(path):
					dict1[dir]['video'].append(lists)
				if dict1[dir]=={'photo':[],'video':[]}:
					shutil.rmtree(os.path.join(basepath,session.get('username'),dir))
					del dict1[dir]
			dirs=os.listdir(os.path.join(basepath,session.get('username')))
			dirs.insert(0,'ALL')
			dirs.insert(0,'')
			if session.get('now_folder') not in dirs:
				session['now_folder']=dirs[2:]

			return render_template('album.html',dirs=dirs,colspan=colspan,username=session.get('username'), \
				filefolder=session.get('now_folder'),files=dict1,edit=session.get('edit'))
	
	session['now_folder']=dirs[2:]
	return render_template('album.html',dirs=dirs,colspan=colspan, \
		files=dict2, filefolder=dirs[2:],username=session.get('username'),edit=session.get('edit'))

@app.route('/stream/<folder>/<name>',methods=['GET','POST'])
def stream(folder,name):
	basepath = os.path.join(os.path.dirname(__file__),'static','uploads')
	dirs=os.listdir(os.path.join(basepath,session.get('username')))
	dirs.insert(0,'')

	fileName=[]
	for lists in os.listdir(os.path.join(basepath,session.get('username'),folder,'photo')):
		sub_path = os.path.join(os.path.join(basepath,session.get('username'),folder,'photo'),lists)
		fileName.append(lists)
	for lists in os.listdir(os.path.join(basepath,session.get('username'),folder,'video')):
		sub_path = os.path.join(os.path.join(basepath,session.get('username'),folder,'video'),lists)
		fileName.append(lists)

	if request.method=='POST':
		if request.values['folder'] !='0':
			folder=dirs[int(request.values['folder'])]
			fileName.clear()
			fileName=[]
			for lists in os.listdir(os.path.join(basepath,session.get('username'),folder,'photo')):
				sub_path = os.path.join(os.path.join(basepath,session.get('username'),folder,'photo'),lists)
				fileName.append(lists)
			for lists in os.listdir(os.path.join(basepath,session.get('username'),folder,'video')):
				sub_path = os.path.join(os.path.join(basepath,session.get('username'),folder,'video'),lists)
				fileName.append(lists)
			name=fileName[0]
		elif request.values['next']=='往前':
			name=fileName[(fileName.index(name))-1]
		elif request.values['next']=='往後':
			name=fileName[(fileName.index(name))+1]
		return redirect(url_for('stream',folder=folder,name=name))
	return render_template('stream.html',dirs=dirs,name=name,folder=folder,fileName=fileName,username=session.get('username'))


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Test')
	parser.add_argument('--fd_model_path', default='',
						type=str, help='the path of face detection model')
	parser.add_argument('--fr_backbone_path', default='',
						type=str, help='the path of face recognition backbone')
	parser.add_argument('--fr_model_path', default='',
						type=str, help='the path of face recognition head')
	parser.add_argument('--enroll_dir', default='enroll',
						type=str, help='the path of stored enroll features')
	parser.add_argument('--long_side', default=320, type=int,
						help='when origin_size is false, long_side is scaled size(320 or 640 for long side)')
	parser.add_argument('--confidence_threshold', default=0.3, type=float, help='confidence_threshold for fd')
	parser.add_argument('--top_k', default=2000, type=int, help='top_k')
	parser.add_argument('--nms_threshold', default=0.3, type=float, help='nms_threshold')
	parser.add_argument('--keep_top_k', default=1000, type=int, help='keep_top_k')
	parser.add_argument('--fr_threshold', default=-1.4387, type=float, help='fr threshold from IJBC 11 1e-4')

	args = parser.parse_args()

	# load FD model
	fd_model = init_FD(args)
	# load FR model
	fr_backbone, fr_head, device = init_FR(args)
	fr_backbone.eval()
	fr_head.eval()

	app.run(host='0.0.0.0',port='8000',debug=True)