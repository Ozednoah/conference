import json,requests
import random
from flask import make_response,render_template,request,redirect,flash,session
from sqlalchemy import desc

from conferenceapp import app,db
from conferenceapp.models import Comments, Myorder, OrderDetails, User,State,Skill,State,Breakout,user_sessions,Contactus,Posts,Payment
from conferenceapp.forms import ContactForm, Loginform
from conferenceapp import Message,mail

@app.route('/')
def home():
    login=Loginform()
    contact=ContactForm()
    id=session.get('loggedin')
    alluserinfo=User.query.get(id)
    all_break=Breakout.query.all()
    #conect to API
    # try:
    #     http = urllib3.PoolManager()
    #     response = http.request('GET', 'http://127.0.0.1:8082/api/v1.0/listall')
    #     #redf = requests.get('http://127.0.0.1:8082/api/v1.0/listall')
    #     #retrieve the json in the request
    #     hostel_json = json.loads(response.data)
    # except:
    #     hostel_json={}
    # #status = hostel_json['status']# to pick the status
    return render_template('user/index.html',login=login,alluserinfo=alluserinfo,all_break=all_break,contact=contact)

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='GET':
        contact=ContactForm()
        fed=Skill.query.all()
        feds=State.query.all()
        return render_template('user/register.html',fed=fed,feds=feds,contact=contact)
    else:
        email=request.form.get('email')
        pwd1=request.form.get('pwd1')
        pwd2=request.form.get('pwd2')
        fname=request.form.get('fname')
        lname=request.form.get('lname')
        state=request.form.get('state')
        skill=request.form.get('skill')
        if email=='' or pwd1=='' or pwd2=='' or fname=='' or lname=='' or state=='' or skill=='':
            flash('please complete the form')
            return redirect('/register')
        elif pwd1!=pwd2:
            flash('passwords do not match')
            return redirect('/register')
        else:
            p=User(user_fname=fname,user_email=email,user_pass=pwd1,user_lname=lname,user_stateid=state,user_skillid=skill)
            db.session.add(p)
            db.session.commit()
            id=p.user_id
            session['loggedin']=id
            return redirect('/userhome')

@app.route('/userhome')
def userhome():
    logstatus=session.get('loggedin')
    contact=ContactForm()
    if logstatus == None:
        return redirect('/')
    else:
        alluserinfo=db.session.query(User).get(logstatus)
        return render_template('user/userhome.html',alluserinfo=alluserinfo,contact=contact)

@app.route('/logout')
def logout():
    session.pop('loggedin')
    return redirect('/')

@app.route('/user/login',methods=['POST'])
def submit_login():
    login=Loginform()
    contact=ContactForm()
    username=request.form.get('username')
    pwd=login.pwd.data
    #validate
    if login.validate_on_submit():
        deets = User.query.filter(User.user_email==username, User.user_pass==pwd).first()
        if deets:
            id=deets.user_id
            session['loggedin']=id
            return redirect('/userhome')
            #return render_template('user/demo.html',deets=deets)
        else:
            flash('login failed please register')
            return redirect('/')
    else:
        return render_template('user/index.html',login=login,contact=contact)

@app.route('/user/breakout')
def user_breakout():
    sess=session.get('loggedin')
    contact=ContactForm()
    if sess==None:
        return redirect('/')
    else:
        alluserinfo=User.query.get(sess)
        skillinfo=alluserinfo.user_skillid
        breaksess=Breakout.query.filter(Breakout.break_skillid==skillinfo).all()
        return render_template('user/breakout.html',alluserinfo=alluserinfo,breaksess=breaksess,contact=contact)

@app.route('/user/pay/breakout')
def pay_user_breakout():
    sess=session.get('loggedin')
    contact=ContactForm()
    if sess==None:
        return redirect('/')
    else:
        alluserinfo=User.query.get(sess)
        skillinfo=alluserinfo.user_skillid
        breaksess=Breakout.query.filter(Breakout.break_skillid==skillinfo).all()
        return render_template('user/paybreak.html',alluserinfo=alluserinfo,breaksess=breaksess,contact=contact)

@app.route('/user/paybreak',methods=['POST',"GET"])
def user_pay():
    loggedin = session.get('loggedin')
    if loggedin == None:
        return redirect("/")
    if request.method=='POST':
        #retrieve form data, breakout ids
        bid = request.form.getlist('bid')

        #insert new recd into myorder,
        mo = Myorder(order_userid=loggedin)
        db.session.add(mo)
        db.session.commit()
        orderid = mo.order_id
        #generate a trans ref using random (save in session), insert into payment table
        ref = int(random.random() * 10000000)
        session['refno'] = ref
        #loop over the selected breakout ids and insert into
        #order_details, 
        totalamt = 0
        for b in bid:
            breakdeets = Breakout.query.get(b)
            break_amt = breakdeets.break_amt
            totalamt = totalamt + break_amt
            od = OrderDetails(det_orderid=orderid,det_breakid=b,det_breakamt=break_amt)
            db.session.add(od)

        db.session.commit()
        p = Payment(pay_userid=loggedin,pay_orderid=orderid,pay_ref=ref,pay_amt=totalamt)       
        db.session.add(p) 
        db.session.commit()
        return redirect("/user/confirm_breakout")    
    else:
        return redirect("/userhome")

@app.route('/user/confirm_breakout',methods=['GET','POST'])
def confirm_break():
    loggedin = session.get('loggedin')
    ref = session.get('refno')
    if loggedin == None or ref == None:
        return redirect("/")
    userdeets = User.query.get(loggedin) 
    deets = Payment.query.filter(Payment.pay_ref==ref).first() 

    if request.method == 'GET':          
        contactform = ContactForm()                
        return render_template("user/show_breakout_confirm.html",deets = deets,userdeets=userdeets,contactform=contactform)
    else:
        url = "https://api.paystack.co/transaction/initialize"
        
        data = {"email":userdeets.user_email,"amount":deets.pay_amt}
        headers = {"Contentp-Type":"application/json","Authorization":"Bearer sk_test_9ae0a36658673083f2804e54e184c79d151a6d5f"}

        response = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, data=json.dumps(data))

        rspjson = json.loads(response.text)
        if rspjson.get('status')==True:
            authurl=rspjson['data']['authorization_url']
            return redirect(authurl)
        else:
            return 'please try again'
             
        return render_template("user/demo.html",response=rspjson)
    
   


@app.route('/user/breakout/<page>')
def break_details():
    return render_template('breakoutdetails.html')

@app.route('/user/regbreakout',methods=["POST"])
def reg_breakout():
    bid=request.form.getlist('bid')
    userinfo=session.get('loggedin')
    user=User.query.get(userinfo)
    db.session.execute(f'DELETE FROM user_breakout WHERE user_id="{userinfo}"')
    db.session.commit()
    for i in bid:
        #method 1
        #b=user_sessions.insert().values(user_id=userinfo,breakout_id=i)
        #db.session.execute(b)
        #db.session.commit()
        item=Breakout.query.get(i)
        user.mybreakouts.append(item)
        db.session.commit()
    flash('registerd successfully')
    return redirect('/user/breakout')

@app.route('/user/editprofile')
def editprofile():
    sess=session.get('loggedin')
    contact=ContactForm()
    if sess==None:
        return redirect('/')
    else:
        alluserinfo=User.query.get(sess)
        all_levels=Skill.query.all()
        all_states=State.query.all()
        return render_template('user/profile.html',alluserinfo=alluserinfo,all_levels=all_levels,all_states=all_states,contact=contact)

@app.route('/user/update/<page>',methods=['POST','GET'])
def user_update(page):
    sess=session.get('loggedin')
    if sess==None:
        return redirect('/')
    if request.method=="GET":
        return redirect('/')
    fname=request.form.get('fname')
    lname=request.form.get('lname')
    skill=request.form.get('skill')
    phoneno=request.form.get('phoneno')
    address=request.form.get('address')
    state=request.form.get('state')
    if int(sess)==int(page):
        user=User.query.get(sess)
        user.user_fname=fname
        user.user_lname=lname
        user.user_skillid=skill
        user.user_phone=phoneno
        user.user_address=address
        user.user_stateid=state
        db.session.commit()
        flash('submitted successfully')
    return redirect('/user/editprofile')

@app.route('/contact/info',methods=['GET','POST'])
def contact_info():
    c=ContactForm()
    name=request.args.get('name')
    email=request.args.get('email')
    message=request.args.get('message')
    push=Contactus(contact_name=name,contact_email=email,contact_message=message)
    db.session.add(push)
    db.session.commit()
    cid = push.contact_id
    if cid:
        return json.dumps({'id':cid,'msg':'message sent'})
    else:
        return 'sorry try again'

@app.route('/demo/available')
def available():
    return render_template('user/check_ava.html') 

@app.route('/check/result')
def check_result():
    user = request.args.get('us')
    deets = User.query.filter(User.user_email==user).all()
    if deets:
        return 'username taken'
    else:
        return 'username is available'

@app.route('/check/lga')
def check_lga():
    states=State.query.all()
    return render_template('user/load_lga.html',states=states)

@app.route('/demo/lga',methods=['POST'])
def demo_lga():
    state = request.form.get('stateid')
    rsp = db.session.execute(f"SELECT * FROM lga  WHERE state_id={state}")
    result = rsp.fetchmany(20)
    select_html = '<select>'
    for x,y,z in result:
        select_html = select_html + f"<option value='{x}'>{z}</option>"

    select_html = select_html + '</select>'
    return select_html

@app.route('/user/discussion')
def discussion():
    contact = ContactForm()
    sess = session.get('loggedin')
    if sess==None:
        return redirect('/')
    else:
        alluserinfo = User.query.get(sess)
        posts = Posts.query.all()
        return render_template('user/discussion.html',alluserinfo = alluserinfo,posts = posts,contact=contact)

@app.route('/post/details/<int:page>')
def post_details(page):
    contact = ContactForm()
    sess = session.get('loggedin')
    
    alluserinfo = User.query.get(sess)
    if sess==None:
        return redirect('/')
    else:
        posts = Posts.query.get(page)
        commentdeets = db.session.query(Comments).filter(Comments.c_postid==id).order_by(desc(Comments.c_date)).all()
        return render_template('user/postdetail.html',posts=posts,alluserinfo=alluserinfo,contact=contact,commentdeets=commentdeets)

@app.route('/post/comment',methods=['POST'])
def post_comment():
    sess = session.get('loggedin',0)
    postid = request.form.get('postid')
    comment = request.form.get('comment')
    c = Comments()
    db.session.add(c)
    c.c_userid = sess
    c.c_post_id = postid
    c.c_comment = comment
    db.session.commit()
    #,mthod 2
    # c = Comments(c_userid=sess,
    # c_post_id=postid,
    # c_comment=comment)
    # db.session.add(c)
    # db.session.commit()
    #method3
    # user=User.query.get(sess)
    # dpost=Posts.query.get(postid)
    # c=Comments()
    # db.session.add(c)
    # user.user_comments.append(c)
    # dpost.posts_comments.append(c)
    # c.c_comment=comment
    # db.session.commit()
    return comment

@app.route('/user/donation',methods=['GET','POST'])
def donate():
    if request.method=="GET":
        return render_template('user/donate.html')
    else:
        name=request.form.get('name')
        email=request.form.get('email')
        amt=request.form.get('amt')
        ref = int(random.random() * 10000000)
        session['refno']=ref
        db.session.execute(f"INSERT INTO donation SET fullname='{name}',email='{email}',amt='{amt}',status='pending',ref='{ref}'")
        db.session.commit()
        return redirect('/confirmpay')

@app.route('/confirmpay')
def confirmpay():
    sess=session.get('refno')
    qry=db.session.execute(f'SELECT * FROM donation where ref={sess}')
    data=qry.fetchone()
    return render_template('user/payconfirm.html',data=data)


@app.route('/sendmail')
def sendmail():
    subject = "Automated Email"
    sender = 'Admin@conference.com'
    recipient = ['oz_my_boy@yahoo.com']
    try:
        # msg = Message(subject=subject,sender=sender,recipients=recipient,body='<b>this is a sample email sent from python app</b>')
        # method 2
        msg = Message()
        msg.subject = subject
        msg.sender = sender
        msg.body = 'TEst message again'
        msg.recipients=recipient
        #sending HTML
        htmlstr = "<div><h1 style ='color:red'>Thank you for signing up</h1><p>you have subscribed....<br>Signed by admin</p><img src='https://thumbs.dreamstime.com/z/cup-cofee-top-heart-117247683.jpg' width='100px'></div>"
        msg.html = htmlstr
        with app.open_resource("mywebpage.pdf") as fp:
            #what you wan to save it as when it gets there
            msg.attach('dash.pdf','application/pdf',fp.read())
        mail.send(msg)
        return "mail sent"
    except:
        return "Connection refused"