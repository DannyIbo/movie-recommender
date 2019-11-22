from flask import Flask, render_template, request
from src.modules import create_engine_load_data, setup_nmf, process_user_input

engine, df_data = create_engine_load_data()

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/select')
def select(df_data=df_data):
    user_input = request.args.items()
    # user_input = result_dictionary.values()

    guesses_list = []
    for ui in user_input:
        print(len(ui[1]))
        if ui[1]:
            guesses = process_user_input(ui, df_data)
            guesses_list.append(guesses)
            print(guesses)

    return render_template(
        'select.html',
        guesses_list=guesses_list,
        user_input=user_input
        # result_dictionary=result_dictionary
    )

@app.route('/test')
def test():
    language = request.args.get('language')
    return f'{language}'

if __name__ == '__main__':
    app.run(debug=True)
