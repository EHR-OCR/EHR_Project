from django.shortcuts import render, redirect
from django.http import HttpResponse
import pyrebase

from django.views.generic import View   
from rest_framework.views import APIView
from rest_framework.response import Response

import traceback
from datetime import date
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from plotly.offline import plot
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px

import json

from django.core.files.storage import FileSystemStorage
import mimetypes

import os as os123

import pandas as pd

from pdf2image import convert_from_path
import easyocr
import numpy as np

from django.core.files.storage import default_storage


reader = easyocr.Reader(['en'])


cred = credentials.Certificate("path_to_service_account")
firebase_admin.initialize_app(cred)


config={
	"apiKey": "",
	"authDomain": "",
	"databaseURL": "",
	"projectId": "",
	"storageBucket": "",
	"messagingSenderId": "",
	"appId": "",
	"measurementId": "",
	"serviceAccount": ""
}


config1={
	"apiKey": "",
	"authDomain": "",
	"databaseURL": "",
	"projectId": "",
	"storageBucket": "",
	"messagingSenderId": "",
	"appId": "",
	"measurementId": ""
}

# Initialising database,auth and firebase for further use
firebase=pyrebase.initialize_app(config)
authe = firebase.auth()
database=firebase.database()

db = firestore.client()

storage = firebase.storage()


firebase1=pyrebase.initialize_app(config1)
storage1 = firebase1.storage()

import datetime
from datetime import date



def signIn(request):
	return render(request,"Login.html")

def start(request):
	return render(request,"Start.html")

def home(request):
	doc_list = request.session['doc_list']
	uid = request.session['UID']
	fname = request.session['fname']
	lname = request.session['lname'] 
	age = request.session['age'] 
	email = request.session['email'] 
	gender = request.session['gender'] 
	if(len(doc_list)>0):
		return render(request,"Home.html",{"fname":fname, "lname":lname, "age":age, "UID":uid, "doc_list": doc_list,"email":email,"gender":gender, "check_doctor": "Doctor"})
	return render(request,"Home.html", {"fname": fname,"lname": lname, "age":age,"email":email,"gender":gender, "doc_list": doc_list})

def docHome(request):
	uid = request.session['UID']
	fname = request.session['fname']
	lname = request.session['lname'] 
	patient_list = request.session['patient_list']
	return render(request,"HomeDoctor.html",{"UID":uid, "fname":fname, "lname":lname, "patient_list":patient_list})

def hrHome(request):
	return render(request,"HomeHealthResearcher.html", {"UID":uid, "fname":fname, "lname":lname,"email":email})


# method to read all patients for the doctor which is displayed in the doctor home page
def docProfile(request):
	uid = request.session['UID']
	fname = request.session['fname']
	lname = request.session['lname'] 
	age = request.session['age'] 
	email = request.session['email'] 
	gender = request.session['gender']

	doc_list = []
	result = db.collection("User Information").document(uid).collection("Doctors").stream()
	for doc in result:
		docId = str(doc.id)
		result1 = db.collection("User Information").document(docId).get()
		if(result1.exists):
			res = result1.to_dict()
			fname1 = str(res["First Name"])
			lname1 = str(res["Last Name"])
			dEmail1 = str(res["Email"])
			doc_list.append(["Dr. "+fname1+" "+lname1, dEmail1])	
	request.session['doc_list'] = doc_list
	if(len(doc_list)>0):
		return render(request,"DocProfile.html",{"email":email, "UID":uid,"fname":fname, "lname":lname, "age":age, "gender":gender,"doc_list":doc_list, "check_doctor": "Doctor"})
	return render(request,"DocProfile.html",{"email":email, "UID":uid,"fname":fname, "lname":lname, "age":age, "gender":gender, "doc_list": doc_list})

# method to upload document and other information to the database based on user id
def uploadDoc(request):
	if request.method == 'POST' and request.FILES['myfile']:
		storage1 = firebase1.storage()
		myfile = request.FILES['myfile']
		myfile1 = str(myfile)
		m = myfile1.split('.')[-1]
		if m != "pdf":
			return render(request, 'UploadDoc.html', {"message": "Invalid report format!"})

		try:
			uid = str(request.session['UID'])
			rbcCount = float(request.POST.get("rbcCount"))
			wbcCount = int(request.POST.get("wbcCount"))
			pltCount = int(request.POST.get("pltCount"))
			ham = float(request.POST.get("haemo"))
		except:
			print("Reaced Here")
			file_name = default_storage.save("report.pdf", myfile)
			images = convert_from_path("report.pdf", 500, poppler_path = 'path_to_poppler_binary_file')
			bounds = reader.readtext(np.array(images[0]), min_size = 0, slope_ths = 0.2, ycenter_ths = 0.7, height_ths = 0.6, width_ths = 0.8, decoder = 'beamsearch', beamWidth = 10)

			text = ''
			context = {}
			for i in range(len(bounds)):
				text = text + bounds[i][1] + '\n'
				l = text.split("\n")
			for i in range(len(l)):
				if(l[i] == "Name"):
					print("Name: "+l[i+1])
				if(l[i].find("Name")!=-1):
					print("Name: "+l[i].split(":")[1].strip())
				if(l[i] == "Haemoglobin"):
					context["Haemoglobin"] = l[i+1].strip().split()[0]
				if(l[i] == "Total Count (WBC)"):
					context["WBC"] = l[i+1].strip().split()[0]
				if(l[i] == "Total Count (RBC)"):
					context["RBC"] = l[i+1].strip().split()[0]
				if(l[i] == "Platelet Count"):
					context["Platelet"] = l[i+1].strip().split()[0]
				if(l[i] == "Reporting Date"):
					dt = l[i+1].strip().split("/")
					da = "20"+dt[-1]+"-"+dt[1]+"-"+dt[0]
					context["date"] = da
			os123.remove("report.pdf")
			return render(request, 'UploadDoc.html', context)
		dt = str(request.POST.get("Reportdate"))
		age = int(calculateAge(dt))
		up = {"Test Name": "CBC", "Lab Name": "Lab Name", "Age": age, "Haemoglobin": ham, "RBC": rbcCount, "WBC": wbcCount, "Platelet": pltCount}
		db.collection("User Information").document(uid).collection("Reports").document(dt).set(up)
		path_on_cloud = uid+"/"+dt+"/"+"report.pdf"
		storage1.child(path_on_cloud).put(myfile)
		return render(request, 'UploadDoc.html', {"message": "Uploaded Document Successfully"})

	return render(request, 'UploadDoc.html')
	


# method to remove doctor from patients list. validation: doctor can be removed only if the doctor already exists in the list
def removeDoctor(request):
	fname = request.session['fname']
	lname = request.session['lname'] 
	age = request.session['age'] 
	email = request.session['email'] 
	gender = request.session['gender']
	doc_list = request.session['doc_list']
	email1=str(request.POST.get('docRemoveEmail'))
	uid = request.session['UID']
	ut = str(request.session['User Type'])
	
	print(email)
	f = 0
	for i in range(len(doc_list)):
		dEmail = doc_list[i][1]
		if(dEmail == email1):
			del doc_list[i]
			f = 1
			break
	if(f == 0):
		message = "Doctor does not exist in list"

		if ut == "Doctor":
			if(len(doc_list)>0):
				return render(request,"DocProfile.html",{"fname":fname, "lname":lname, "age":age, "UID":uid, "doc_list": doc_list,"email":email,"gender":gender, "check_doctor": "Doctor", "message": message})
			return render(request,"DocProfile.html", {"fname": fname,"lname": lname, "age":age,"email":email,"gender":gender, "doc_list": doc_list, "message": message})

		if(len(doc_list)>0):
			return render(request,"Home.html",{"fname":fname, "lname":lname, "age":age, "UID":uid, "doc_list": doc_list,"email":email,"gender":gender, "check_doctor": "Doctor", "message": message})
		return render(request,"Home.html", {"fname": fname,"lname": lname, "age":age,"email":email,"gender":gender, "doc_list": doc_list, "message": message})


	result = db.collection("User Information").stream()
	docId = ""
	for doc in result:
		d = doc.to_dict()
		docId = str(doc.id)
		dEmail2 = str(d["Email"])
		if(dEmail2 == email1):
			break
	db.collection("User Information").document(uid).collection("Doctors").document(docId).delete()
	db.collection("User Information").document(docId).collection("Patients").document(uid).delete()

	request.session['doc_list'] = doc_list

	if ut == "Doctor":
		if(len(doc_list)>0):
			return render(request,"DocProfile.html",{"fname":fname, "lname":lname, "age":age, "UID":uid, "doc_list": doc_list,"email":email,"gender":gender, "check_doctor": "Doctor"})
		return render(request,"DocProfile.html", {"fname": fname,"lname": lname, "age":age,"email":email,"gender":gender, "doc_list": doc_list})		

	if(len(doc_list)>0):
			return render(request,"Home.html",{"fname":fname, "lname":lname, "age":age, "UID":uid, "doc_list": doc_list,"email":email,"gender":gender, "check_doctor": "Doctor"})
	return render(request,"Home.html", {"fname": fname,"lname": lname, "age":age,"email":email,"gender":gender, "doc_list": doc_list})


# method to add doctor to the patients doctor's list. validations: doctor should be registered as a doctor in the application and should not have already been added 
def addDoctor(request):
	fname_og = request.session['fname']
	lname_og = request.session['lname'] 
	age = request.session['age'] 
	email_og = request.session['email'] 
	gender = request.session['gender']
	doc_list = request.session['doc_list']
	email=str(request.POST.get('docEmail'))
	uid = request.session['UID']
	ut = str(request.session['User Type'])
	print(uid)
	print(email)
	if(len(email) == 0):
		message = "Please enter email id"
		if ut == "Doctor":
			if(len(doc_list)>0):
				return render(request,"DocProfile.html",{"fname":fname_og, "lname":lname_og, "age":age, "UID":uid, "doc_list": doc_list,"email":email_og,"gender":gender, "check_doctor": "Doctor", "message": message})
			return render(request,"DocProfile.html", {"fname": fname_og,"lname": lname_og, "age":age,"email":email_og,"gender":gender, "doc_list": doc_list, "message": message})
		
		if(len(doc_list)>0):
			return render(request,"Home.html",{"fname":fname_og, "lname":lname_og, "age":age, "UID":uid, "doc_list": doc_list,"email":email_og,"gender":gender, "check_doctor": "Doctor", "message": message})
		return render(request,"Home.html", {"fname": fname_og,"lname": lname_og, "age":age,"email":email_og,"gender":gender, "doc_list": doc_list, "message": message})
	
	for i in doc_list:
		if(i[1].lower() == email.lower()):
			message = "Doctor already added to the list"
			if ut == "Doctor":
				if(len(doc_list)>0):
					return render(request,"DocProfile.html",{"fname":fname_og, "lname":lname_og, "age":age, "UID":uid, "doc_list": doc_list,"email":email_og,"gender":gender, "check_doctor": "Doctor", "message": message})
				return render(request,"DocProfile.html", {"fname": fname_og,"lname": lname_og, "age":age,"email":email_og,"gender":gender, "doc_list": doc_list, "message": message})	

			if(len(doc_list)>0):
				return render(request,"Home.html",{"fname":fname_og, "lname":lname_og, "age":age, "UID":uid, "doc_list": doc_list,"email":email_og,"gender":gender, "check_doctor": "Doctor", "message": message})
			return render(request,"Home.html", {"fname": fname_og,"lname": lname_og, "age":age,"email":email_og,"gender":gender, "doc_list": doc_list, "message": message})	

	result = db.collection("User Information").stream()
	docId = ""
	message = ""
	flag = 0
	dEmail = ""
	dFirstName = ""
	dLastName = ""
	for doc in result:
		d = doc.to_dict()
		docId = str(doc.id)
		dEmail = str(d["Email"])
		if(dEmail == email):
			uType = str(d["User Type"])
			if(uType == "Doctor"):
				dFirstName = str(d["First Name"])
				dLastName = str(d["Last Name"])
				flag = 1
				break
			else:
				flag = 1
				message = "User not registered as doctor"
				break
	if(len(message)>0):
		if ut == "Doctor":
			if(len(doc_list)>0):
				return render(request,"DocProfile.html",{"fname":fname_og, "lname":lname_og, "age":age, "UID":uid, "doc_list": doc_list,"email":email_og,"gender":gender, "check_doctor": "Doctor", "message": message})
			return render(request,"DocProfile.html", {"fname": fname_og,"lname": lname_og, "age":age,"email":email_og,"gender":gender, "doc_list": doc_list, "message": message})		

		if(len(doc_list)>0):
			return render(request,"Home.html",{"fname":fname_og, "lname":lname_og, "age":age, "UID":uid, "doc_list": doc_list,"email":email_og,"gender":gender, "check_doctor": "Doctor", "message": message})
		return render(request,"Home.html", {"fname": fname_og,"lname": lname_og, "age":age,"email":email_og,"gender":gender, "doc_list": doc_list, "message": message})		

	if(flag == 0):
		message = "User does not exist"
		if ut == "Doctor":
			if(len(doc_list)>0):
				return render(request,"DocProfile.html",{"fname":fname_og, "lname":lname_og, "age":age, "UID":uid, "doc_list": doc_list,"email":email_og,"gender":gender, "check_doctor": "Doctor", "message": message})
			return render(request,"DocProfile.html", {"fname": fname_og,"lname": lname_og, "age":age,"email":email_og,"gender":gender, "doc_list": doc_list, "message": message})		

		if(len(doc_list)>0):
			return render(request,"Home.html",{"fname":fname_og, "lname":lname_og, "age":age, "UID":uid, "doc_list": doc_list,"email":email_og,"gender":gender, "check_doctor": "Doctor", "message": message})
		return render(request,"Home.html", {"fname": fname_og,"lname": lname_og, "age":age,"email":email_og,"gender":gender, "doc_list": doc_list, "message": message})		

	if(flag == 1):
		data = {docId: docId}
		db.collection("User Information").document(uid).collection("Doctors").document(docId).set(data)
		data = {uid: uid}
		db.collection("User Information").document(docId).collection("Patients").document(uid).set(data)
		doc_list.append(["Dr. "+dFirstName+" "+dLastName, dEmail])
		request.session['doc_list'] = doc_list
		
	if ut == "Doctor":
		if(len(doc_list)>0):
			return render(request,"DocProfile.html",{"fname":fname_og, "lname":lname_og, "age":age, "UID":uid, "doc_list": doc_list,"email":email_og,"gender":gender, "check_doctor": "Doctor"})
		return render(request,"DocProfile.html", {"fname": fname_og,"lname": lname_og, "age":age,"email":email_og,"gender":gender, "doc_list": doc_list})

	if(len(doc_list)>0):
		return render(request,"Home.html",{"fname":fname_og, "lname":lname_og, "age":age, "UID":uid, "doc_list": doc_list,"email":email_og,"gender":gender, "check_doctor": "Doctor"})
	return render(request,"Home.html", {"fname": fname_pg,"lname": lname_og, "age":age,"email":email_og,"gender":gender, "doc_list": doc_list})


# Method to sign in user to the correct home page based on user type registered
def postsignIn(request):
	email=request.POST.get('email')
	request.session['email'] = email
	pasw=request.POST.get('pass')
	try:
		# if there is no error then signin the user with given email and password
		user=authe.sign_in_with_email_and_password(email,pasw)
	except:
		message="Invalid Credentials!!Please Check your Data"
		return render(request,"Login.html",{"message":message})
	session_id=user['idToken']
	request.session['uid']=str(session_id)
	uid = str(user['localId']) 
	user_id = uid
	print("Us: "+user_id)
	print(uid)
	result = db.collection("User Information").document(uid).get()
	if(result.exists):
		res = result.to_dict()
		fname = res["First Name"]
		lname = res["Last Name"]
		age = calculateAge(res["DOB"])
		gender = res["Gender"]
		try:
			request.session['fname'] = fname
			request.session['lname'] = lname
			request.session['UID'] = uid
			request.session['age'] = age
			request.session['email'] = email
			request.session['gender'] = gender
			
		except:
			print("already added")
		if(res['User Type'] == "Patient"):
			request.session['User Type'] = "Patient"
			
			doc_list = []

			result = db.collection("User Information").document(uid).collection("Doctors").stream()
			for doc in result:
				docId = str(doc.id)
				result1 = db.collection("User Information").document(docId).get()
				if(result1.exists):
					res = result1.to_dict()
					fname1 = str(res["First Name"])
					lname1 = str(res["Last Name"])
					dEmail = str(res["Email"])
					doc_list.append(["Dr. "+fname1+" "+lname1, dEmail])	

			request.session['doc_list'] = doc_list
			fname = request.session['fname']

			print("first name : "+fname)
			if(len(doc_list) == 0):
				return render(request,"Home.html",{"fname":fname, "lname":lname, "age":age, "UID":uid, "doc_list": doc_list,"email":email,"gender":gender})
			return render(request,"Home.html",{"fname":fname, "lname":lname, "age":age, "UID":uid, "doc_list": doc_list,"email":email,"gender":gender,"check_doctor": "Doctor"})

		elif(res['User Type'] == "Doctor"):
			request.session['User Type'] = "Doctor"

			
			patient_list = []
			result = db.collection("User Information").document(uid).collection("Patients").stream()
			for doc in result:
				docId = str(doc.id)
				result1 = db.collection("User Information").document(docId).get()
				if(result1.exists):
					res = result1.to_dict()
					fname1 = str(res["First Name"])
					lname1 = str(res["Last Name"])
					dob = str(res["DOB"])
					age = calculateAge(dob)	
					pEmail = str(res["Email"])
					gender = str(res["Gender"])
					patient_list.append([""+fname1+" "+lname1, pEmail, age, gender, docId])	

			request.session['patient_list'] = patient_list
			return render(request,"HomeDoctor.html",{"email":email, "UID":uid, "fname":fname, "lname":lname, "age":age, "gender":gender, "patient_list": patient_list})

		elif(res['User Type'] == "Health Researcher"):
			request.session['User Type'] = "Health Researcher"
			return render(request,"HomeHealthResearcher.html",{"email":email, "UID":uid, "fname":fname, "lname":lname})

		else:
			message="Something Went Wrong, Could not Login"
			return render(request,"Login.html",{"message":message})

def logout(request):
	try:
		del request.session['uid']
	except:
		pass
	return render(request,"Start.html")

def signUp(request):
	return render(request,"Registration.html")


# Method to add users to the database after proper validation is done
def postsignUp(request):
	firstname = request.POST.get('firstName')
	if(firstname == None):
		return render(request, "Registration.html", {"message": "Invalid First Name Entered"})
	firstname = str(firstname)
	if(len(firstname)==0):
		return render(request, "Registration.html", {"message": "Invalid First Name Entered"})
	lastname = request.POST.get('lastName')
	if(lastname == None):
		return render(request, "Registration.html", {"message": "Invalid Last Name Entered"})
	lastname = str(lastname)
	if(len(lastname)==0):
		return render(request, "Registration.html", {"message": "Invalid Last Name Entered"})
	dob = str(request.POST.get('birthdayDate'))
	gender = str(request.POST.get('Gender'))
	if(gender == "1"):
		gender = "Male"
	elif(gender == "2"):
		gender = "Female"
	elif(gender == "3"):
		gender = "Non-Binary"
	elif(gender == "4"):
		gender = "Transgender"
	elif(gender == "5"):
		gender = "Intersex"
	elif(gender == "6"):
		gender = str(request.POST.get('othergender'))
	elif(gender == "7"):
		gender = "I prefer not to say"
	else:
		gender = ""
	if(len(gender) == 0):
		return render(request, "Registration.html", {"message": "Invalid Gender Specified"})
	userType = str(request.POST.get('userType'))
	if(userType == "1"):
		userType = "Patient"
	elif(userType == "2"):
		userType = "Doctor"
	elif(userType == "3"):
		userType = "Health Researcher"
	else:
		userType = ""
	if(len(userType) == 0):
		return render(request, "Registration.html", {"message": "Please specify correct User Type"})
	email = str(request.POST.get('email'))
	passs = request.POST.get('pass')
	if(passs == None):
		return render(request, "Registration.html", {"message": "Enter Password Field"})
	passs = str(passs)
	if(len(passs) == 0):
		return render(request, "Registration.html", {"message": "Enter Password Field"})

	if(len(passs) < 6):
		return render(request, "Registration.html", {"message": "Weak Password, Has to be atleast 6 characters long"})

	repeat_pass = request.POST.get('confirm_password')
	if(repeat_pass == None):
		return render(request, "Registration.html", {"message": "Enter Repeat Password Field"})
	repeat_pass = str(repeat_pass)
	if(len(repeat_pass) == 0):
		return render(request, "Registration.html", {"message": "Enter Repeat Password Field"})
	try:
		# creating a user with the given email and password
		user=authe.create_user_with_email_and_password(email,passs)
		uid = str(user['localId'])
		##idtoken = request.session['uid']
		print(uid)
		data = {"First Name": firstname, 'Last Name': lastname, "DOB": dob, "Gender": gender, "User Type": userType, "Email": email}
		db.collection("User Information").document(uid).set(data)
		today = str(date.today())
		db.collection("Logs").document(today).set({uid: "Created Account"})
		if(gender == "Male" and userType == "Patient"):
			db.collection("Male").document("Male").set({uid: uid})
		elif(gender == "Female" and userType == "Patient"):
			db.collection("Female").document("Female").set({uid:uid})
		elif(userType == "Patient"):
			db.collection("Others").document("Others").set({uid:uid})
	except Exception:
		print("Reached Here")
		traceback.print_exc()
		return render(request, "Registration.html", {"message": "Error Occurred, Please try again"})
	return render(request,"Login.html")


# Method to get patient health data and display in dashboard
def pDash(request):
	
	# References - 
	# https://plotly.com/python/px-arguments/
	# https://plotly.com/python/dropdowns/
	# https://plotly.com/python/plotly-express/
	# https://community.plotly.com/t/dropdowns-in-plotly-express-chart-filtering-default-button/62976

	# px works primarily with dataframes. Input requires df

	ut = str(request.session['User Type'])
	print("User type: "+ut)
	print("UID: "+request.session["UID"])
	uid = request.session["UID"]
	
	report_list = []
	sl = storage.list_files()
	for sld in sl:
		h = str(sld).split(",")[1].strip()[:-1]
		g = h.split("/")
		l = [g[1], 'CBC Report', h]
		x123 = h.split("/")[0]
		if(x123==uid):
			report_list.append(l)
			print(h)

	result = db.collection("User Information").document(uid).collection("Reports").stream()
	tm = []
	rbc = []
	wbc = []
	plat = []
	hm = []
	for doc in result:
		d = doc.to_dict()
		tm.append(str(doc.id))
		rbc.append(d["RBC"])
		wbc.append(d["WBC"])
		plat.append(d["Platelet"])
		hm.append(d["Haemoglobin"])


	if(len(tm) == 0):
		if ut == "Doctor":
			return render(request, 'PatientDashboard.html', 
                  context={'plot_check': "No Documents added","Doctor": "Doctor", "report_list": report_list})
		return render(request, 'PatientDashboard.html', 
                  context={'plot_check': "No Documents added", "report_list": report_list}) 

	df = pd.DataFrame(dict(Time= tm, 
	RBC = rbc,
	WBC = wbc,
	Platelet = plat,
	Haemoglobin = hm))

	# data from different dataframes can also be taken. Refer to the first link in case of different df's
	fig = go.Figure()
	fig.add_traces(go.Scatter(x=df['Time'].astype(dtype=str), y=df['RBC'], marker_color = 'red', visible = True, mode = 'lines+markers'))
	fig.add_traces(go.Scatter(x=df['Time'].astype(dtype=str), y=df['WBC'], marker_color = 'orange', visible = False, mode = 'lines+markers'))
	fig.add_traces(go.Scatter(x=df['Time'].astype(dtype=str), y=df['Platelet'], marker_color = 'green', visible = False, mode = 'lines+markers'))
	fig.add_traces(go.Scatter(x=df['Time'].astype(dtype=str), y=df['Haemoglobin'], marker_color = 'purple', visible = False, mode = 'lines+markers'))
	
	fig.update_xaxes(
		rangeslider_visible=True,
		rangeselector=dict(
			buttons=list([
				dict(count=1, label="1m", step="month", stepmode="backward"),
				dict(count=6, label="6m", step="month", stepmode="backward"),
				dict(count=1, label="YTD", step="year", stepmode="todate"),
				dict(count=1, label="1y", step="year", stepmode="backward"),
				dict(step="all")
			])
		)
	)

	updatemenus = [
		dict(
			buttons = list([
				dict(label = "RBC",method = "update", args = [{"visible":[True,False,False,False]}]),
				dict(label = "WBC",method = "update", args = [{"visible":[False,True,False,False]}]),
				dict(label = "Platelet",method = "update", args = [{"visible":[False,False,True,False]}]),
				dict(label = "Haemoglobin",method = "update",  args = [{"visible":[False,False,False,True]}]),
			]),
			direction="down",
			pad={"r": 0, "t": 0, "l":0, "b":0},
			showactive=False,
			x=0.89,
			xanchor="left",
			y=1.2,
			yanchor="top",
		),
	]

	fig.update_layout(updatemenus=updatemenus, showlegend = False)

	plot_div = plot({'data': fig}, output_type='div')

	if ut == "Doctor":
		return render(request, 'PatientDashboard.html', 
                  context={'plot_div': plot_div, "report_list":report_list,"Doctor": "Doctor"})
	return render(request, 'PatientDashboard.html', 
                  context={'plot_div': plot_div, "report_list":report_list })

# method to download the uploaded report
def downloadReport(request):
	path = str(request.POST.get("reportPath"))
	print(path)
	storage = firebase.storage()
	storage.download(path = path, filename="report.pdf")
	
	fl = "path_to_root_dir"
	filename = "report.pdf"
	fl_path = fl + filename
	fl = open(fl_path, 'rb').read()
	response = HttpResponse(fl, content_type = 'application/pdf')
	response['Content-Disposition'] = "attachment; filename=%s" % filename

	os123.remove(fl_path)

	return response

def docPatientHome(request):
	email = request.session['email']
	uid = request.session["UID"]
	fname = request.session['fname']
	lname = request.session['lname']
	age = request.session['age']
	gender = request.session['gender']
	patient_list = request.session['patient_list']
	return render(request,"HomeDoctor.html",{"email":email, "UID":uid, "fname":fname, "lname":lname, "age":age, "gender":gender, "patient_list": patient_list})

# method to view patient timeline based on number of records stored per year in the patients name.
def viewPatient(request):
	uid = str(request.POST.get("PatientID"))
	result = db.collection("User Information").document(uid).collection("Reports").stream()
	

	report_list = []
	sl = storage.list_files()
	for sld in sl:
		h = str(sld).split(",")[1].strip()[:-1]
		g = h.split("/")
		l = [g[1], 'CBC Report', h]
		x123 = h.split("/")[0]
		if(x123==uid):
			report_list.append(l)
			print(h)


	tm = []
	rbc = []
	wbc = []
	plat = []
	hm = []
	for doc in result:
		d = doc.to_dict()
		tm.append(str(doc.id))
		rbc.append(d["RBC"])
		wbc.append(d["WBC"])
		plat.append(d["Platelet"])
		hm.append(d["Haemoglobin"])


	if(len(tm) == 0):
		return render(request, 'PatientDashboard.html', context={'plot_check': "No Documents added", "Patient": "Patient", "report_list": report_list}) 

	df = pd.DataFrame(dict(Time= tm, 
	RBC = rbc,
	WBC = wbc,
	Platelet = plat,
	Haemoglobin = hm))

	# data from different dataframes can also be taken. Refer to the first link in case of different df's
	fig = go.Figure()
	fig.add_traces(go.Scatter(x=df['Time'].astype(dtype=str), y=df['RBC'], marker_color = 'red', visible = True, mode = 'lines+markers'))
	fig.add_traces(go.Scatter(x=df['Time'].astype(dtype=str), y=df['WBC'], marker_color = 'orange', visible = False, mode = 'lines+markers'))
	fig.add_traces(go.Scatter(x=df['Time'].astype(dtype=str), y=df['Platelet'], marker_color = 'green', visible = False, mode = 'lines+markers'))
	fig.add_traces(go.Scatter(x=df['Time'].astype(dtype=str), y=df['Haemoglobin'], marker_color = 'purple', visible = False, mode = 'lines+markers'))
	
	fig.update_xaxes(
		rangeslider_visible=True,
		rangeselector=dict(
			buttons=list([
				dict(count=1, label="1m", step="month", stepmode="backward"),
				dict(count=6, label="6m", step="month", stepmode="backward"),
				dict(count=1, label="YTD", step="year", stepmode="todate"),
				dict(count=1, label="1y", step="year", stepmode="backward"),
				dict(step="all")
			])
		)
	)

	updatemenus = [
		dict(
			buttons = list([
				dict(label = "RBC",method = "update", args = [{"visible":[True,False,False,False]}]),
				dict(label = "WBC",method = "update", args = [{"visible":[False,True,False,False]}]),
				dict(label = "Platelet",method = "update", args = [{"visible":[False,False,True,False]}]),
				dict(label = "Haemoglobin",method = "update",  args = [{"visible":[False,False,False,True]}]),
			]),
			direction="down",
			pad={"r": 0, "t": 0, "l":0, "b":0},
			showactive=False,
			x=0.89,
			xanchor="left",
			y=1.2,
			yanchor="top",
		),
	]

	fig.update_layout(updatemenus=updatemenus, showlegend = False)

	plot_div = plot({'data': fig}, output_type='div')


	return render(request, 'PatientDashboard.html', 
                  context={'plot_div': plot_div, "Patient": "Patient", "report_list": report_list})



# method to check for all validations when health researcher submits form request and generate and download the file accordingly
def hrDownload(request):

	email = request.session['email']
	uid = request.session["UID"]
	fname = request.session['fname']
	lname = request.session['lname']

	male = str(request.POST.get("male"))
	female = str(request.POST.get("female"))
	others = str(request.POST.get("others"))

	gn = []

	if(len(male) == 0):
		gn.append("Male")
	if(len(female) == 0):
		gn.append("Female")
	if(len(others) == 0):
		gn.append("Others")

	minAge = float(request.POST.get("minAge"))
	maxAge = float(request.POST.get("maxAge"))

	if(minAge > maxAge):
		message = "Minimum age greater than maximum age"
		return render(request,"HomeHealthResearcher.html",{"email":email, "UID":uid, "fname":fname, "lname":lname, "message": message})

	if(len(gn) == 0):
		message = "Please select atleast one gender"
		return render(request,"HomeHealthResearcher.html",{"email":email, "UID":uid, "fname":fname, "lname":lname, "message": message})


	pid_final = []
	p = 0
	dob_final = []
	gender_final = []
	dor_final = []
	rbc_final = []
	wbc_final = []
	Haemoglobin_final = []
	Platelet_final = []

	result = db.collection("User Information").stream()
	for doc in result:
		d = doc.to_dict()
		d1 = str(doc.id)
		result1 = db.collection("User Information").document(d1).get()
		if(result1.exists):
			res = result1.to_dict()
			dob = str(res["DOB"])
			g = str(res["Gender"])
			a = calculateAge(dob)
			a = float(a)
			if(a>= minAge and a<=maxAge):
				if(g == "Male" and "Male" in gn):
					# add values to list
					p = p + 1
					reports = db.collection("User Information").document(d1).collection("Reports").stream()
					for r in reports:
						col = r.to_dict()
						date = str(r.id)
						test = db.collection("User Information").document(d1).collection("Reports").document(date).get()
						if(test.exists):
							cbc = test.to_dict()
							pid_final.append(p)
							dob_final.append(dob)
							gender_final.append(g)
							dor_final.append(date)
							rbc = float(cbc["RBC"])
							rbc_final.append(rbc)
							wbc = int(cbc["WBC"])
							wbc_final.append(wbc)
							pl = int(cbc["Platelet"])
							Platelet_final.append(pl)
							hm = float(cbc["Haemoglobin"])
							Haemoglobin_final.append(hm)

				elif(g == "Female" and "Female" in gn):
					# add values to list
					p = p + 1
					reports = db.collection("User Information").document(d1).collection("Reports").stream()
					for r in reports:
						col = r.to_dict()
						date = str(r.id)
						test = db.collection("User Information").document(d1).collection("Reports").document(date).get()
						if(test.exists):
							cbc = test.to_dict()
							pid_final.append(p)
							dob_final.append(dob)
							gender_final.append(g)
							dor_final.append(date)
							rbc = float(cbc["RBC"])
							rbc_final.append(rbc)
							wbc = int(cbc["WBC"])
							wbc_final.append(wbc)
							pl = int(cbc["Platelet"])
							Platelet_final.append(pl)
							hm = float(cbc["Haemoglobin"])
							Haemoglobin_final.append(hm)
				elif("Others" in gn):
					# add values to list
					p = p + 1
					reports = db.collection("User Information").document(d1).collection("Reports").stream()
					for r in reports:
						col = r.to_dict()
						date = str(r.id)
						test = db.collection("User Information").document(d1).collection("Reports").document(date).get()
						if(test.exists):
							cbc = test.to_dict()
							pid_final.append(p)
							dob_final.append(dob)
							gender_final.append(g)
							dor_final.append(date)
							rbc = float(cbc["RBC"])
							rbc_final.append(rbc)
							wbc = int(cbc["WBC"])
							wbc_final.append(wbc)
							pl = int(cbc["Platelet"])
							Platelet_final.append(pl)
							hm = float(cbc["Haemoglobin"])
							Haemoglobin_final.append(hm)


	df1 = {"Patient ID": pid_final, "Date Of Birth": dob_final, "Gender": gender_final, "Date of Report": dor_final, "RBC": rbc_final, "WBC": wbc_final,
	"Haemoglobin": Haemoglobin_final, "Platelet": Platelet_final}

	df = pd.DataFrame(df1)
	name = "EHR.csv"

	df.to_csv(name, index = False)

	path = "path_to_root_dir"
	fl_path = path + name
	fl = open(fl_path, 'r')
	mime_type, _ = mimetypes.guess_type(fl_path)
	response = HttpResponse(fl, content_type=mime_type)
	response['Content-Disposition'] = "attachment; filename=%s" % name
	os123.remove(fl_path)
	return response


def timeline(request):
	
	uid = request.session["UID"]
	ut = str(request.session["User Type"])
	result = db.collection("User Information").document(uid).collection("Reports").stream()
	dd = {}
	for doc in result:
		d = doc.to_dict()
		d1 = str(doc.id)
		d1 = d1.split("-")[0]
		if(d1 in dd):
			dd[d1] = dd[d1] + 1
		else:
			dd[d1] = 1

	x = []
	y = []

	for k, v in dd.items():
		x.append(k)
		y.append(v)

	if(len(x) == 0):
		if ut == "Doctor":
			return render(request, 'PatientTimeline.html', 
                  context={'plot_check': "not there","Doctor": "Doctor"}) 
		return render(request, 'PatientTimeline.html',context={'plot_check': "not there"})

	fig = go.Figure()
	fig.add_trace(go.Bar(x=x, y=y, xperiodalignment="start"))
	graphs = []
	graphs.append(
        go.Bar(x=x, y=y, xperiodalignment="start")
    )
	fig.update_xaxes(title_text="Year")
	fig.update_yaxes(title_text="Count")
	
    # Setting layout of the figure.
	layout = go.Layout(hovermode = "x unified")
	
	plot_div = plot({'data': fig, 'layout': layout}, 
                    output_type='div')
					
	if ut == "Doctor":
		return render(request, 'PatientTimeline.html', 
                  context={'plot_div': plot_div,"Doctor": "Doctor"})
	return render(request, 'PatientTimeline.html',context={'plot_div': plot_div})


def calculateAge(born):
    born = datetime.datetime.strptime(born, '%Y-%m-%d').date()
    today = date.today()
    try:
        birthday = born.replace(year = today.year)
 
    # raised when birth date is February 29
    # and the current year is not a leap year
    except ValueError:
        birthday = born.replace(year = today.year,
                  month = born.month + 1, day = 1)
 
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year