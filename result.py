import streamlit as st
from firebase_admin import credentials, db, initialize_app
import firebase_admin
import time

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

        try:
            firebase_admin.get_app('turing_test_app')  # 初期化済みか確認
        except ValueError:
            initialize_app(cred, {
                'databaseURL': database_url,
            }, name='turing_test_app')

        st.session_state.firebase_app = True
    except Exception as e:
        st.error(f"Firebaseの初期化に失敗しました: {e}")


def show_result_page():
    st.title("チューリングテスト - 結果とチャット履歴")

    # Firebaseの参照
    ref_results = db.reference('results', app=firebase_admin.get_app('turing_test_app'))

    try:
        evaluation_results = ref_results.get()
        if evaluation_results:
            for result_id, result_data in evaluation_results.items():
                # 評価結果の表示
                st.subheader("評価結果")
                st.write(f"**判定結果:** {result_data.get('identity', '未設定')}")
                st.write(f"**確信度:** {result_data.get('confidence', 0)}/10")
                st.write(f"**判断理由:** {result_data.get('reason', '理由が記載されていません')}")
                st.write(f"**会話相手:** {result_data.get('talk_mode', '不明')}")
                correct = result_data.get('correct', False)
                st.write(f"**正解:** {'正解' if correct else '不正解'}")
                st.write(f"**ターン数:** {result_data.get('turn_count', 0)}")
                time_taken = result_data.get('time_taken', 0)
                minutes, seconds = divmod(int(time_taken), 60)
                st.write(f"**会話時間:** {minutes}分 {seconds}秒")
                # チャット履歴の表示
                st.subheader("チャット履歴")
                st.write(f"**お題:** {result_data.get('topic', '未設定')}")
                st.write("**会話内容:**")
                messages = result_data.get('messages', [])
                for message in messages:
                    st.write(f"[{message['role']}] {message['content']}")
                st.divider()
        else:
            st.info("評価結果とチャット履歴はまだ保存されていません。")
    except Exception as e:
        st.error(f"データの取得中にエラーが発生しました: {e}")
