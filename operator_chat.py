import streamlit as st
from firebase_admin import credentials, db, initialize_app
import time
import firebase_admin

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
            app = firebase_admin.get_app('operator_chat_app')  # アプリ名で取得
        except ValueError:
            app = initialize_app(cred, {
                'databaseURL': database_url,
            }, name='operator_chat_app')  # アプリ名で初期化

        st.session_state.firebase_app = True

    except Exception as e:
        st.error(f"Firebaseの初期化に失敗しました: {str(e)}")

# セッションステートの初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_topic" not in st.session_state:
    st.session_state.current_topic = "未設定"

# ページ構成
st.title("Operator Chat")
st.subheader(f"現在のお題: {st.session_state.current_topic}")

ref = db.reference('chats', app=firebase_admin.get_app('operator_chat_app'))

all_messages = ref.get()


with st.chat_message("user"):
    st.markdown(all_messages)
st.session_state.messages.append({"role": "user", "content": all_messages})

with st.chat_message("assistant"):
            message_placeholder = st.empty()

# メッセージ取得関数
def get_pending_messages():
    return ref.order_by_child('status').equal_to('pending').get()

# 1秒ごとにデータを更新
while True:
    messages = get_pending_messages()

    # 未応答のメッセージを表示
    if messages:
        for message_id, message_data in messages.items():
            st.write(f"新しいメッセージ (Topic: {message_data.get('topic', 'N/A')}):")
            st.text(message_data.get('content', 'No content'))

            with st.chat_message("operator"):
                message_placeholder = st.empty()
                response = st.text_input("返信を入力してください", key=message_id)  # ここにユニークなkeyを設定

                try:
                    if response:
                        ref.child(message_id).update({
                            'response': response,
                            'status': 'responded',
                            'response_time': time.time(),
                            'role': 'operator'
                        })
                        st.success("返信が送信されました。")
                        message_placeholder.markdown(response)

                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    full_response = "An error occurred while sending the response."
    else:
        st.write("未応答のメッセージはありません。")

    # 会話履歴の表示
    st.subheader("会話履歴")
    all_messages = ref.get()
    if all_messages:
        for msg_id, msg_data in all_messages.items():
            st.markdown(f"- **{msg_data['role'].capitalize()}**: {msg_data['content']}")
    else:
        st.write("会話履歴はありません。")

    # Firebaseの履歴を全消しするボタン
    if st.button("履歴を全消し"):
        ref.delete()  # chatsノードを全削除
        st.success("Firebaseの履歴が全て削除されました。")

    # 1秒ごとに再実行
    time.sleep(1)
    st.experimental_rerun()
