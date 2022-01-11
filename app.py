from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)

#=============================================

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
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        return render_template('mainPage.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return render_template('index.html')

@app.route('/postingPage')
def post():
    return render_template('postingPage.html')

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
        cur_cnt = cur_cnt + 1
        print(cur_cnt)
        cur_cnt = str(cur_cnt)
        print(cur_cnt)
        db.childcare.update_one({'title': title_receive}, {'$set': {'cur_cnt': cur_cnt}})
        msg = "신청이 완료 되었습니다!"

    return jsonify({'msg': msg})

@app.route('/detail', methods=['GET'])
def read_reviews():
    board_title = request.args.get('title')
    board_info = db.childcare.find_one({'title': '@@아파트'}, {'_id': False})

    return render_template('detail.html', title=board_info['title'],location=board_info['location'], population=board_info['population'],details=board_info['details'],cur_cnt=board_info['cur_cnt'], age=board_info['age'],phone=board_info['phone'])

@app.route('/postingPage', methods=['POST'])
def save_post():
    title_receive = request.form["title_give"]
    phone_receive = request.form["phone_give"]
    population_receive = request.form["population_give"]
    age_receive = request.form["age_give"]
    location_receive = request.form["location_give"]
    details_receive = request.form["details_give"]

    doc = {
        "title":title_receive,
        "phone":phone_receive,
        "population":population_receive,
        "age":age_receive,
        "location":location_receive,
        "details":details_receive,
        "cur_cnt": "0"
    }

    db.childcare.insert_one(doc)
    return jsonify({"msg":"게시글이 등록되었습니다"})

@app.route('/postingPage', methods=['DELETE'])
def delete_post():
    post_receive = request.form["post_give"]
    title_receive = request.form["title_give"]
    phone_receive = request.form["phone_give"]
    population_receive = request.form["population_give"]
    age_receive = request.form["age_give"]
    location_receive = request.form["locationpost_give"]
    details_receive = request.form["details_give"]

    doc = {
        "post": post_receive,
        "title": title_receive,
        "phone": phone_receive,
        "population": population_receive,
        "age": age_receive,
        "location": location_receive,
        "details": details_receive,
    }
    db.childcare.insert_one(doc)
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
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
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
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "profile_name": username_receive,                           # 프로필 이름 기본값은 아이디
        "profile_pic": "",                                          # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png", # 프로필 사진 기본 이미지
        "profile_info": ""                                          # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

