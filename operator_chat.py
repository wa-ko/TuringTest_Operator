import streamlit as st
from firebase_admin import credentials, db, initialize_app
import time
import firebase_admin
from result import show_result_page


# セッションステートの初期化
if 'page' not in st.session_state:
    st.session_state.page = 'chat'
if "messages" not in st.session_state:
    st.session_state.messages = []
if "talk_mode" not in st.session_state:
    st.session_state.talk_mode = "AI"
if "current_topic" not in st.session_state:
    st.session_state.current_topic = "未設定"

# Firebaseの初期化
if 'firebase_app' not in st.session_state:
    try:
        firebase_config = {
            "type": st.secrets["firebase"]["type"],
            "project_id": st.secrets["firebase"]["project_id"],
            "private_key_id": st.secrets["firebase"]["private_key_id"],
            "private_key": st.secrets["firebase"]["private_key"],
            "client_email": st.secrets["firebase"]["client_email"],
            "client_id": st.secrets["firebase"]["client_id"],
            "auth_uri": st.secrets["firebase"]["auth_uri"],
            "token_uri": st.secrets["firebase"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
        }

        database_url = st.secrets["firebase"]["database_url"]

        cred = credentials.Certificate(firebase_config)

        # Firebaseが初期化済みかどうかを確認
        try:
            app = firebase_admin.get_app('turing_test_app')  # アプリ名で取得
        except ValueError:
            app = initialize_app(cred, {
                'databaseURL': database_url,
            }, name='turing_test_app')  # アプリ名で初期化

        st.session_state.firebase_app = True

    except Exception as e:
        st.error(f"Firebaseの初期化に失敗しました: {str(e)}")

# Firebaseデータベースの参照
ref_chats = db.reference('chats', app=firebase_admin.get_app('turing_test_app'))
config_ref = db.reference('config', app=firebase_admin.get_app('turing_test_app'))

# サイドバーにページ切り替えボタンを追加

if st.sidebar.button('設定ページへ'):
    st.session_state.page = 'setting'

if st.sidebar.button('チャットページへ'):
    st.session_state.page = 'chat'

if st.sidebar.button('結果ページへ'):
    st.session_state.page = 'result'

if st.session_state.page == 'setting':
        # 会話モードの切り替えスイッチ
    talk_mode = st.radio("会話相手を選択してください", ("AI", "人間"), index=0 if st.session_state.talk_mode == "AI" else 1)
    if talk_mode != st.session_state.talk_mode:
        st.session_state.talk_mode = talk_mode
        config_ref.update({"talk_mode": talk_mode})
    if talk_mode == "人間":
        chat_placeholder = st.container()
    if st.button("Firebaseのchatsを削除"):
        try:
            ref_chats.delete()
            st.success("Firebaseのchatsノードを削除しました。")
        except Exception as e:
            st.error(f"chatsノードの削除中にエラーが発生しました: {e}")

if st.session_state.page == 'chat':
    # ページ構成
    st.title("Operator Chat")
    st.subheader(f"現在のお題: {st.session_state.current_topic}")

    chat_placeholder = st.container()
    # チャット履歴の取得と表示
    with chat_placeholder:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    all_messages = ref_chats.get()
    st.session_state.current_topic = "未設定"
    if "data_fetched" not in st.session_state:
        if all_messages:
            st.session_state.messages = []
            for msg_id, msg_data in all_messages.items():
                st.session_state.messages.append(
                    {"role": "user", "content": msg_data['content']})

                role = msg_data['role']
                if role == "operator":
                    role = "assistant"
                if 'response' in msg_data:
                    st.session_state.messages.append(
                        {"role": "assistant", "content": msg_data['response']})

                if "current_topic" not in st.session_state:
                    st.session_state.current_topic = "未設定"
                else:
                    st.session_state.current_topic = msg_data.get('topic', '未設定')
        # データが取得されたことをフラグとして設定
        st.session_state.data_fetched = True
    response = st.chat_input("ここに入力してください")
    if response:
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        latest_message_id = list(all_messages.keys())[-1]
        # Save operator response to Firebase
        ref_chats.child(latest_message_id).update({
            'response': response,
            'status': 'responded',
            'response_time': time.time(),
            'role': 'operator'
        })
    with st.chat_message("user"):
        message_placeholder = st.empty()
        try:
            while True:
                message_data = ref_chats.order_by_child('status').equal_to('pending').limit_to_last(1).get()
                if message_data:
                    # 最新のメッセージを取得
                    latest_message_id = list(message_data.keys())[0]
                    human_message = message_data[latest_message_id].get('content')
                    if message_data[latest_message_id].get('status') == 'pending':
                        break
                else:
                    continue

            message_placeholder.markdown(human_message or "No response available.")
            st.session_state.messages.append({"role": "user", "content": human_message or "No response available."})
        except Exception as e:
            st.error(f"An error occurred: {e}")
            operator_response = "An error occurred while fetching the message."

elif st.session_state.page == 'result':
    show_result_page()