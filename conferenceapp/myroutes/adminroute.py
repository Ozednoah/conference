import math, random, os
from flask import make_response,render_template,request,redirect,flash,session
from werkzeug.security import generate_password_hash, check_password_hash
from conferenceapp import app,db
from conferenceapp.models import Admin, User,State,Skill,State,Breakout
from conferenceapp.forms import Loginform

@app.route('/admin/login')
def adminlogin():
    return render_template('admin/login.html')

@app.route('/admin/submit/login',methods=["POST"])
def submit_adminlogin():
    user=request.form.get('username')
    pwd=request.form.get('pwd')
    if user=='' or pwd=='':
        flash('complete the fields')
        return render_template('admin/login.html')
    else:
        facts=Admin.query.filter(Admin.admin_username==user).first()
        formatedpwd=facts.admin_password
        chk=check_password_hash(formatedpwd,pwd)


        if chk:
            session['adminlog']=facts.admin_id
            return redirect('/admin/page')
        else:
            flash('invalid credentials')
            return render_template('admin/login.html')

# @app.route('/admin/submit/login',methods=["POST"])
# def submit_adminlogin():
#     user=request.form.get('username')
#     pwd=request.form.get('pwd')
#     if user=='' or pwd=='':
#         flash('complete the fields')
#         return render_template('admin/login.html')
#     else:
#         facts=Admin.query.filter(Admin.admin_username==user, Admin.admin_password==pwd).first()
#         if facts:
#             id=Admin.admin_id
#             session['adminlog']=facts.admin_id
#             return redirect('/admin/page')
#         else:
#             flash('invalid credentials')
#             return render_template('admin/login.html')



@app.route('/admin/page')
def adminpage():
    sess=session.get('adminlog')
    if sess==None:
        return redirect('/admin/login')
    else:
        sess1=db.session.query(Admin).get(sess)
        return render_template('admin/index.html',sess=sess,sess1=sess1)
#how file upload works

@app.route('/admin/upload',methods=["GET","POST"])
def admin_upload():
    sess=session.get('adminlog')
    if sess==None:
        return redirect('/admin/login')
    if request.method=='GET':
        return render_template('admin/test.html')
    else:
        data=request.files.get('image')
        orijoname=data.filename
        #ext=orijoname.split('.')
        ext=os.path.splitext(orijoname)
        fn=math.ceil(random.random()*10000)
        save_as=str(fn)+ext[1]
        #check your extension type
        allowed=['.jpg','.png','.gif']
        if ext[1].lower() in allowed:
            data.save(f'conferenceapp/static/assets/img/{save_as}')
            return 'submitted'
        else:
            return 'file type not supported'

@app.route('/admin/breakout')
def adminbreak():
    sess=session.get('adminlog')
    if sess==None:
        return redirect('/admin/login')
    else:
        all_breakouts=Breakout.query.all()
        return render_template('admin/breakout.html',all_breakouts=all_breakouts)

@app.route('/admin/addbreakout', methods=['GET','POST'])
def addbreakout():
    sess=session.get('adminlog')
    if sess==None:
        return redirect('/admin/login')
    if request.method =='GET':
        skills = Skill.query.all()
        return render_template('admin/addbreakout.html', skills=skills)
    else:
        #Retrieve form data (request.form....)
        title = request.form.get('title')
        level = request.form.get('skill')
        #request file
        pic_object = request.files.get('image')
        original_file =  pic_object.filename
        if title =='' or level =='':
            flash("Title and Level cannot be empty")
            return redirect('/admin/addbreakout')
        if original_file !='': #check if file is not empty
            extension = os.path.splitext(original_file)
            if extension[1].lower() in ['.jpg','.png']:
                fn = math.ceil(random.random() * 100000000)  
                save_as = str(fn)+extension[1] 
                pic_object.save(f"conferenceapp/static/assets/img/{save_as}")
                #insert other details into db
                b = Breakout(break_title=title,break_picture=save_as,break_skillid=level)
                db.session.add(b)
                db.session.commit()            
                return redirect("/admin/breakout")
            else:
                flash('File Not Allowed')
                return redirect("/admin/addbreakout")

        else:
            save_as =""
            b = Breakout(break_title=title,break_picture=save_as,break_skillid=level)
            db.session.add(b)
            db.session.commit() 
            return redirect("/admin/breakout")

@app.route('/admin/breakout/delete/<page>')
def adminbreakoutdelete(page):
    sess=session.get('adminlog')
    if sess==None:
        return redirect('/admin/login')
    else:
        b=db.session.query(Breakout).get(page)
        db.session.delete(b)
        db.session.commit()
        flash(f'breakout session {page} deleted')
        return redirect('/admin/breakout')

@app.route('/admin/signout')
def admin_signout():
    session.pop('adminlog')
    return redirect('/admin/login')

@app.route('/admin/reg')
def admin_reg():
    #users=db.session.query(User,State,Skill).join(State).join(Skill).all()
    users=User.query.join(State).join(Skill).add_columns(State,Skill).filter(Skill.skill_id==1).all()
    #outerjoin
    #users = User.query.outerjoin(State,User.user_stateid==State.state_id).add_columns(State).all()
    return render_template('admin/allusers.html',users=users)

@app.route('/admin/signup',methods=["GET","POST"])
def admin_signup():
    if request.method=='GET':
        return render_template('admin/adminsignup.html')
    else:
        user=request.form.get('username')
        pwd=request.form.get('pwd')
        pwd2=request.form.get('pwd2')
        if pwd==pwd2:
            formated=generate_password_hash(pwd)
            ad=Admin(admin_username=user,admin_password=formated)
            db.session.add(ad)
            db.session.commit()
            flash('New user signed up')
            return redirect('/admin/login')
        else:
            flash('the passwords do not match')
            return redirect('/admin/signup')