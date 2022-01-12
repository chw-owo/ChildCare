from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

client = MongoClient('localhost', 27017)
db = client.childcare

SECRET_KEY = 'ChildCare'
## 메인페이지
@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    posts = db.childcare.find({})
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"id":payload["id"]})
        return render_template('mainPage.html', user_info=user_info, posts=posts)
    except jwt.ExpiredSignatureError:
        return render_template('mainPage.html', posts=posts) #redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return render_template('mainPage.html', user_info=0, posts=posts)

@app.route('/postingPage')
def post():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"id": payload["id"]})
        return render_template('postingPage.html', user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg=""))
    except jwt.exceptions.DecodeError:
        return render_template('mainPage.html',user_info=0)

## 신청하기
@app.route('/detail', methods=['POST'])
def apply():
    title_receive = request.form['title_give']

    board = db.childcare.find_one({'title':title_receive})

    cur_cnt = int(board['cur_cnt'])
    max_cnt = int(board['population'])
    msg = ""

    if cur_cnt == max_cnt:
        msg = "모집이 완료된 글 입니다."
    else:
        token_receive = request.cookies.get('mytoken')
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        apply_name = db.users.find_one({"id":payload["id"]})['id']
        apply_list = board['apply_info']
        apply_list.append(apply_name)
        cur_cnt = cur_cnt + 1
        cur_cnt = str(cur_cnt)
        db.childcare.update_one({'title': title_receive}, {'$set': {'cur_cnt': cur_cnt}})
        db.childcare.update_one({'title': title_receive}, {'$set': {'apply_info': apply_list}})

@app.route('/detail', methods=['GET'])
def detail():
    board_title = request.args.get('title')
    board_info = db.childcare.find_one({'title': board_title}, {'_id': False})
    token_receive = request.cookies.get('mytoken')

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"id":payload["id"]})
        return render_template('detail.html', title=board_info['title'], location=board_info['location'],
                               cur_cnt=board_info['cur_cnt'], population=board_info['population'], desc=board_info['details'],
                               age=board_info['age'], phone=board_info['phone'],
                               post_info=board_info['post_info'], user_info=user_info, apply_info=board_info['apply_info'])

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg=""))
    except jwt.exceptions.DecodeError:
        return render_template('mainPage.html',user_info=0)

@app.route('/detail', methods=['UPDATE'])
def cancel():
    title_receive = request.form["title_give"]
    cancel_name = request.form["cancel_name"]

    board = db.childcare.find_one({'title': title_receive})
    cur_cnt = int(board['cur_cnt'])
    apply_list = board['apply_info']

    apply_list.remove(cancel_name)

    cur_cnt = cur_cnt - 1;
    cur_cnt = str(cur_cnt)

    db.childcare.update_one({'title': title_receive}, {'$set': {'cur_cnt': cur_cnt}})
    db.childcare.update_one({'title': title_receive}, {'$set': {'apply_info': apply_list}})

    return jsonify({"msg":"신청이 취소되었습니다!"})

@app.route('/postingPage', methods=['POST'])
def save_post():

    token_receive = request.cookies.get('mytoken')

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"id": payload["id"]})
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return render_template('mainPage.html', user_info=0)

    post_info_receive = request.form["post_info_give"]
    title_receive = request.form["title_give"]
    phone_receive = request.form["phone_give"]
    population_receive = request.form["population_give"]
    age_receive = request.form["age_give"]
    location_receive = request.form["location_give"]
    details_receive = request.form["details_give"]

    doc = {
        "post_info": post_info_receive,
        "title":title_receive,
        "phone":phone_receive,
        "population":population_receive,
        "age":age_receive,
        "location":location_receive,
        "details":details_receive,
        "cur_cnt": "0",
        "apply_info": []
    }

    db.childcare.insert_one(doc)


    return render_template('postingPage.html', user_info=user_info)

@app.route('/detail', methods=['DELETE'])
def delete_post():

    title_receive = request.form["title_give"]
    db.childcare.delete_one({"title":title_receive})

    return jsonify({"msg":"게시글이 삭제되었습니다"})

@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'id': username_receive, 'pw': pw_hash})

    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60*60)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "id": username_receive,                               # 아이디
        "pw": password_hash                                  # 비밀번호
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"id": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

