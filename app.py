from flask import *

from flask_bootstrap import Bootstrap

from flask_pymongo import PyMongo

from flask_moment import Moment

from datetime import datetime

from bson.objectid import ObjectId

from passlib.hash import sha256_crypt



app= Flask('the-login-system')

app.config['SECRET_KEY']='ThE_lOgIn_sYsTeM'

#app.config['MONGO_URI'] = 'mongodb://localhost:27017/bankaccount-db'


app.config['MONGO_URI'] ='mongodb+srv://richardlin:richardlin@cluster0-4kl8t.azure.mongodb.net/bankaccount?retryWrites=true&w=majority'
monent=Moment(app)

Bootstrap(app)
mongo = PyMongo(app)

@app.route('/',methods =['GET','POST'])
def register():
    if request.method == 'GET':
        session['user-info']=None
        return render_template('register.html')
    elif request.method == 'POST':
        doc = {}
        '''for item in request.form:
            doc[item] = request.form[item]
        '''
        doc = {'email': request.form['email']}
        found = mongo.db.users.find_one(doc)
        if found is None:
            doc['firstname']=request.form['firstname']
            doc['lastname'] = request.form['lastname']
            doc['password'] = sha256_crypt.encrypt(request.form['password'])
            doc['time'] = datetime.utcnow()
            doc['amount'] = 0
            mongo.db.users.insert_one(doc)
            flash('Account created successfully!')
            return redirect('/login')
        else:
            flash('user name is taken, try another.')
            return redirect('/')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        doc = {'email':request.form['email']}
        found = mongo.db.users.find_one(doc)

        print('found',found)
        if found is None:
            flash('Here is no such user, Please sign up right now.')
            return redirect('/')
        else:
            passcode = found['password']
        # if the combination is incorrect
        if found is None and len(passcode) < 50:
            flash ('Here is no such user, Please sign up right now.')
            return redirect('/')
        else:
            try:

                if sha256_crypt.verify(request.form['password'], found['password']):
                    session['user-info'] = {'firstname': found['firstname'], 'lastname': found['lastname'],'email': found['email'], 'loginTime': datetime.utcnow(),'amount':found['amount']}

                    return redirect('/home')
                else:
                    flash('The email and password you entered did not match our record. Please double check and try again.')
                    return redirect('/login')
            except ValueError:
                flash('please sign up ')
                return redirect('/')

@app.route('/forgot',methods = ['GET','POST'])
def forgot():
    if request.method == 'GET':
        return render_template('forgotpassword.html')
    elif request.method == 'POST':
        doc = {'email': request.form['email']}
        found = mongo.db.users.find_one(doc)

        print('found', found)
        if found is None:
            flash('Here is no such user, Please sign up right now.')
            return redirect('/')
        New_password = request.form['New_password']
        Confirm_password = request.form['Confirm_password']
        if New_password == Confirm_password:
            password = sha256_crypt.encrypt(New_password)
        else:
            flash('Passwords you entered not match. Please try again.')
            return redirect('/forgot')
        mongo.db.users.update_one({'email': doc['email']},{'$set': {'password': password}})
        return redirect('/login')

@app.route('/home',methods=['GET','POST'])
def home():
    if 'user-info' in session:
        savedEntries = mongo.db.users.find({'email': session['user-info']['email']})
        records = mongo.db.record.find({'email': session['user-info']['email']})
        info = [x for x in savedEntries]

        record_info = [x for x in records]
        #print(record_info)
        if request.method == 'GET':
            print('info',record_info)
            return render_template('home.html',entry=info, records = record_info)
        elif request.method == 'POST':
            balance = info[0]['amount']
            amount = request.form['amount']
            choice = request.form['choice']
            #print('amount',amount)
            if choice == 'clear' and amount=='':
                balance = 0
                mongo.db.users.update_one({'email': session['user-info']['email']}, {'$set': {'amount': balance}})
                mongo.db.users.update_one({'email': session['user-info']['email']}, {'$set': {'time': datetime.utcnow()}})
                mongo.db.record.drop()
                return redirect('/logout')
            if amount.isalpha():
                flash('Invalided Entry')
                return redirect('/home')
            if amount =='':
                flash('Please enter amount.')
                return redirect('/home')
            #print('info=',choice, balance,amount)
            amount =int(amount)
            if choice == 'deposit':
                balance += amount
            elif choice == 'withdraw':
                if balance < amount:
                    flash('Sorry, you account is out of balance')
                else:
                    balance -= amount

            print(choice, balance, amount)
            mongo.db.users.update_one({'email': session['user-info']['email']}, {'$set': {'amount': balance}})
            mongo.db.users.update_one({'email': session['user-info']['email']}, {'$set': {'time': datetime.utcnow()}})
            if choice == 'deposit':
                choice = 'deposited'
            elif choice == 'withdraw':
                choice = 'withdrew'

            entry ={'email':session['user-info']['email'],'amount':amount, 'choice':choice,'time':datetime.utcnow()}
            #print(entry)
            mongo.db.record.insert_one(entry)
            return redirect('/home')
    else:
        flash('You need to login first!')
        return redirect('/login')

@app.route('/logout')
def logout():
    # removing user information from the session
    if 'user-info' is session:
        session.pop('user-info',None)
        return redirect('/')
    else:
        return redirect('/')

@app.route('/delete/<id>')
def delete(id):
    found = mongo.db.record.find_one({'_id': ObjectId(id)})
    mongo.db.record.remove(found)
    return redirect('/home')



@app.errorhandler(404)
def page_not_found(e):
	return render_template('error.html',error=e),404

@app.errorhandler(400)
def page_not_found(e):
	return render_template('error.html',error=e),400

@app.errorhandler(500)
def page_not_found(e):
	return render_template('error.html',error=e),500


if __name__=="__main__":
    app.run(host= "https://ancient-brook-99886.herokuapp.com/",debug = True)
    #app.run(debug=True)
