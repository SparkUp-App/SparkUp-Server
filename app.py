from flask import Flask, request, render_template

app = Flask(__name__)


@app.route('/',methods=['GET'])
def factorial():
    a = request.args.get('number')
    factorial = eval(a)
    number = 1
    if factorial!=0:
        for i in range(1,factorial+1):
            number = number*i
    return render_template('factorial.html',**locals())


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run(host="0.0.0.0")
