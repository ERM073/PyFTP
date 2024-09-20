import os
import ftplib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class FTPClient:
    def __init__(self, master):
        self.master = master
        self.master.title("FTPクライアント")
        self.master.geometry("800x600")  # アプリケーションサイズを大きくする

        # FTP情報入力欄を配置
        self.server_label = tk.Label(master, text="FTPサーバー:")
        self.server_label.grid(row=0, column=0, padx=10, pady=(10, 0))
        self.server_entry = tk.Entry(master, width=30)
        self.server_entry.grid(row=0, column=1, padx=10, pady=(10, 5))
        self._add_copy_paste_context_menu(self.server_entry)

        self.user_label = tk.Label(master, text="ユーザー名:")
        self.user_label.grid(row=1, column=0, padx=10, pady=(5, 0))
        self.user_entry = tk.Entry(master, width=30)
        self.user_entry.grid(row=1, column=1, padx=10, pady=(5, 5))
        self._add_copy_paste_context_menu(self.user_entry)

        self.pass_label = tk.Label(master, text="パスワード:")
        self.pass_label.grid(row=2, column=0, padx=10, pady=(5, 0))
        self.pass_entry = tk.Entry(master, show="*", width=30)
        self.pass_entry.grid(row=2, column=1, padx=10, pady=(5, 5))
        self._add_copy_paste_context_menu(self.pass_entry)

        # コネクトボタンを入力欄の下に配置
        self.connect_button = tk.Button(master, text="接続", command=self.connect)
        self.connect_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        # アップロードボタン
        self.upload_button = tk.Button(master, text="ファイルアップロード", command=self.upload_file)
        self.upload_button.grid(row=4, column=0, padx=10, pady=10)

        # ダウンロードボタン
        self.download_button = tk.Button(master, text="ファイルダウンロード", command=self.download_file)
        self.download_button.grid(row=4, column=1, padx=10, pady=10)

        # 削除ボタン
        self.delete_button = tk.Button(master, text="ファイル削除", command=self.delete_file)
        self.delete_button.grid(row=4, column=2, padx=10, pady=10)

        # Treeview for displaying directories and files
        self.tree = ttk.Treeview(master, height=15)  # ツリーの高さを指定
        self.tree.grid(row=5, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')
        self.tree.bind('<Double-1>', self.on_double_click)

        # 更新ボタン
        self.refresh_button = tk.Button(master, text="更新", command=self.refresh_file_list)
        self.refresh_button.grid(row=6, column=0, columnspan=3, padx=10, pady=10)

        self.ftp = None
        self.current_path = '/'

        # グリッドの列と行の比率を設定
        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=2)
        master.grid_columnconfigure(2, weight=1)
        master.grid_rowconfigure(5, weight=1)  # ツリーの行を広げる

    def _add_copy_paste_context_menu(self, entry):
        """右クリックメニューを追加する"""
        menu = tk.Menu(self.master, tearoff=0)
        menu.add_command(label="コピー", command=lambda: self.copy_to_clipboard(entry))
        menu.add_command(label="貼り付け", command=lambda: self.paste_from_clipboard(entry))

        def show_menu(event):
            menu.post(event.x_root, event.y_root)

        entry.bind("<Button-3>", show_menu)  # 右クリックイベントをバインド

    def copy_to_clipboard(self, entry):
        entry.clipboard_clear()
        entry.clipboard_append(entry.get())

    def paste_from_clipboard(self, entry):
        entry.delete(0, tk.END)
        entry.insert(0, entry.clipboard_get())

    def connect(self):
        """FTPサーバーに接続"""
        server = self.server_entry.get()
        user = self.user_entry.get()
        password = self.pass_entry.get()

        try:
            self.ftp = ftplib.FTP(server)
            self.ftp.login(user, password)
            messagebox.showinfo("接続", "FTPサーバーに接続しました。")
            self.refresh_file_list()
            self.keep_alive()  # 接続を維持するメソッドを呼び出す
        except Exception as e:
            messagebox.showerror("エラー", str(e))

    def keep_alive(self):
        """接続を維持するために定期的にNOOPを送信する"""
        if self.ftp:
            try:
                self.ftp.voidcmd("NOOP")
            except Exception as e:
                print(f"Keep-alive エラー: {e}")

        # 60秒ごとに呼び出す
        self.master.after(60000, self.keep_alive)

    def upload_file(self):
        """ローカルファイルをFTPサーバーにアップロード"""
        file_path = filedialog.askopenfilename()

        if file_path:
            file_name = os.path.basename(file_path)
            try:
                with open(file_path, 'rb') as file:
                    self.ftp.storbinary(f'STOR {self.current_path}/{file_name}', file)
                messagebox.showinfo("アップロード", f"{file_name}をアップロードしました。")
                self.refresh_file_list()
            except Exception as e:
                messagebox.showerror("アップロードエラー", str(e))

    def download_file(self):
        """FTPサーバーからファイルをダウンロード"""
        selected_item = self.tree.selection()
        if selected_item:
            selected_file = self.tree.item(selected_item)['text']
            full_path = f"{self.current_path}/{selected_file}"  # 完全なパスを指定

            save_path = filedialog.asksaveasfilename(defaultextension=os.path.splitext(selected_file)[1],
                                                     initialfile=selected_file)

            if save_path:
                try:
                    with open(save_path, 'wb') as file:
                        self.ftp.retrbinary(f'RETR {full_path}', file.write)  # 完全なパスを使用
                    messagebox.showinfo("ダウンロード", f"{selected_file}をダウンロードしました。")
                except Exception as e:
                    messagebox.showerror("ダウンロードエラー", str(e))

    def delete_file(self):
        """FTPサーバーからファイルを削除"""
        selected_item = self.tree.selection()
        if selected_item:
            selected_file = self.tree.item(selected_item)['text']
            full_path = f"{self.current_path}/{selected_file}"  # 完全なパスを指定

            confirm = messagebox.askyesno("削除確認", f"{selected_file}を削除してもよろしいですか？")
            if confirm:
                try:
                    self.ftp.delete(full_path)
                    messagebox.showinfo("削除", f"{selected_file}を削除しました。")
                    self.refresh_file_list()
                except Exception as e:
                    messagebox.showerror("削除エラー", str(e))

    def refresh_file_list(self):
        """FTPサーバー上のファイルリストを表示"""
        if self.ftp:
            self.tree.delete(*self.tree.get_children())
            self.tree.insert('', 'end', self.current_path, text=self.current_path)

            try:
                items = self.ftp.nlst(self.current_path)
                for item in items:
                    if item not in [".", ".."]:
                        self.tree.insert(self.current_path, 'end', item, text=item)
            except ftplib.error_perm as e:
                messagebox.showerror("エラー", str(e))

    def on_double_click(self, event):
        """ディレクトリを開く"""
        selected_item = self.tree.selection()
        if selected_item:
            dir_name = self.tree.item(selected_item)['text']
            if dir_name != self.current_path:
                new_path = f"{self.current_path}/{dir_name}"
                self.current_path = new_path
                self.refresh_file_list()

if __name__ == "__main__":
    root = tk.Tk()
    ftp_client = FTPClient(root)
    root.mainloop()
