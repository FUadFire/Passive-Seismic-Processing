import tkinter as tk
from tkinter import filedialog, messagebox
from obspy import read, Stream, UTCDateTime
import matplotlib.pyplot as plt
import os
from PIL import Image, ImageTk

class SeismicApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Seismic Data Processor")
        self.stream_gabungan = Stream()

        # Direktori simpan gambar sementara
        self.temp_dir = "temp_images"
        os.makedirs(self.temp_dir, exist_ok=True)

        # Frame utama dengan padding
        main_frame = tk.Frame(root, padx=15, pady=15)
        main_frame.pack(fill='both', expand=True)

        # Judul aplikasi
        title = tk.Label(main_frame, text="Software Pengolahan Data Seismik", font=("Arial", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 15), sticky='n')

        # Tombol pilih file
        self.btn_pilih = tk.Button(main_frame, text="Pilih File Seismik (.mseed)", width=30, command=self.pilih_dan_baca_files)
        self.btn_pilih.grid(row=1, column=0, columnspan=3, pady=10)

        # Label info file
        self.label_file_info = tk.Label(main_frame, text="Belum ada file dipilih", font=("Arial", 10))
        self.label_file_info.grid(row=2, column=0, columnspan=3, pady=(0, 20))

        # Input waktu potong frame
        frame_waktu = tk.LabelFrame(main_frame, text="Input Waktu Pemotongan (Format: YYYY-MM-DD HH:MM)", padx=10, pady=10, font=("Arial", 10))
        frame_waktu.grid(row=3, column=0, columnspan=3, sticky='ew')

        tk.Label(frame_waktu, text="Waktu Mulai:", font=("Arial", 10)).grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.entry_mulai = tk.Entry(frame_waktu, width=25, font=("Arial", 10))
        self.entry_mulai.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_waktu, text="Waktu Selesai:", font=("Arial", 10)).grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.entry_selesai = tk.Entry(frame_waktu, width=25, font=("Arial", 10))
        self.entry_selesai.grid(row=1, column=1, padx=5, pady=5)

        # Tombol potong dan plot
        self.btn_potong = tk.Button(main_frame, text="Potong & Plot Data", width=30, font=("Arial", 11, "bold"), command=self.potong_dan_plot)
        self.btn_potong.grid(row=4, column=0, columnspan=3, pady=15)

        # Label status
        self.label_status = tk.Label(main_frame, text="", font=("Arial", 10), fg="green")
        self.label_status.grid(row=5, column=0, columnspan=3, pady=(0, 15))

        # Frame untuk gambar hasil
        frame_gambar = tk.Frame(main_frame)
        frame_gambar.grid(row=6, column=0, columnspan=3)

        # Heading untuk gambar
        tk.Label(frame_gambar, text="Gambar Hasil Penggabungan", font=("Arial", 12, "underline")).grid(row=0, column=0, padx=20)
        tk.Label(frame_gambar, text="Gambar Hasil Pemotongan", font=("Arial", 12, "underline")).grid(row=0, column=1, padx=20)

        # Label untuk gambar dengan border relief
        self.label_img_gabung = tk.Label(frame_gambar, borderwidth=2, relief="groove")
        self.label_img_gabung.grid(row=1, column=0, padx=20, pady=10)

        self.label_img_potong = tk.Label(frame_gambar, borderwidth=2, relief="groove")
        self.label_img_potong.grid(row=1, column=1, padx=20, pady=10)

        # Atur kolom agar proporsional
        main_frame.grid_columnconfigure((0,1,2), weight=1)
        frame_gambar.grid_columnconfigure((0,1), weight=1)

    def pilih_dan_baca_files(self):
        file_paths = filedialog.askopenfilenames(title="Pilih file seismik",
                                                 filetypes=(("MiniSEED files", "*.mseed"), ("All files", "*.*")))
        if not file_paths:
            messagebox.showinfo("Info", "Tidak ada file yang dipilih.")
            self.label_file_info.config(text="Belum ada file dipilih")
            return

        self.stream_gabungan = Stream()
        for file in file_paths:
            try:
                st = read(file)
                self.stream_gabungan += st
            except Exception as e:
                messagebox.showerror("Error", f"Gagal membaca file '{file}': {e}")

        self.label_file_info.config(text=f"{len(file_paths)} file berhasil dibaca, total {len(self.stream_gabungan)} trace.")
        self.label_status.config(text="File berhasil digabung.")

        if len(self.stream_gabungan) > 0:
            fig = self.stream_gabungan.plot(show=False)
            path_gabung = os.path.join(self.temp_dir, "gambar_gabungan.png")
            fig.savefig(path_gabung)
            plt.close(fig)
            self.tampilkan_gambar(path_gabung, self.label_img_gabung)

    def potong_dan_plot(self):
        if len(self.stream_gabungan) == 0:
            messagebox.showwarning("Peringatan", "Belum ada data yang dimuat.")
            return

        mulai_str = self.entry_mulai.get().strip()
        selesai_str = self.entry_selesai.get().strip()

        if not mulai_str or not selesai_str:
            messagebox.showwarning("Peringatan", "Masukkan waktu mulai dan selesai dengan format yang benar.")
            return

        try:
            mulai_waktu = UTCDateTime(mulai_str + ":00")
            selesai_waktu = UTCDateTime(selesai_str + ":00")
        except Exception as e:
            messagebox.showerror("Error", f"Format waktu salah: {e}")
            return

        if mulai_waktu >= selesai_waktu:
            messagebox.showwarning("Peringatan", "Waktu mulai harus lebih kecil dari waktu selesai.")
            return

        potongan = self.stream_gabungan.slice(starttime=mulai_waktu, endtime=selesai_waktu)

        if len(potongan) == 0:
            messagebox.showinfo("Info", "Data pada interval waktu tersebut kosong.")
            return

        fig = potongan.plot(show=False)
        path_potong = os.path.join(self.temp_dir, "gambar_potongan.png")
        fig.savefig(path_potong)
        plt.close(fig)
        self.tampilkan_gambar(path_potong, self.label_img_potong)

        self.label_status.config(text=f"Hasil plot pemotongan disimpan dan ditampilkan.")

    def tampilkan_gambar(self, path, label):
        image = Image.open(path)
        image = image.resize((400, 300))  # Resize agar pas di GUI
        photo = ImageTk.PhotoImage(image)
        label.config(image=photo)
        label.image = photo  # Simpan referensi agar gambar tetap muncul

if __name__ == "__main__":
    root = tk.Tk()
    app = SeismicApp(ro
