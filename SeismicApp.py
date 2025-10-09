import tkinter as tk
from tkinter import filedialog, messagebox
from obspy import read, Stream, UTCDateTime
import matplotlib.pyplot as plt
import os
import pathlib
import numpy as np
import hvsrpy
from PIL import Image, ImageTk

class SeismicApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Passive Seismic Data Processing")
        
        # --- Vars untuk Seismic ---
        self.stream_gabungan = Stream()
        self.stream_potongan = Stream()
        
        # --- Vars untuk HVSR ---
        self.fnames = []
        self.srecords = None
        self.srecords_preprocessed = None
        self.hvsr = None
        
        self.temp_dir = "temp_images"
        self.temp_hvsr_dir = "temp_hvsr"
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.temp_hvsr_dir, exist_ok=True)

        # Setup menubar
        self.menubar = tk.Menu(root)
        root.config(menu=self.menubar)

        # Menu FILE
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="FILE", menu=file_menu)
        file_menu.add_command(label="Pilih File Seismik", command=self.pilih_dan_baca_files)
        file_menu.add_command(label="Potong & Plot Data", command=self.potong_dan_plot)
        file_menu.add_separator()
        file_menu.add_command(label="Simpan Data Gabungan", command=self.simpan_data_gabungan)
        file_menu.add_command(label="Simpan Data Potongan", command=self.simpan_data_potongan)
        file_menu.add_command(label="Simpan Gambar Hasil Trimming", command=self.simpan_figure_hasil_trimming)
        file_menu.add_command(label="Simpan Gambar Hasil Merger", command=self.simpan_figure_hasil_merger)

        # Menu HVSR dan submenu-nya
        self.HVSR_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="HVSR", menu=self.HVSR_menu)
        self.HVSR_menu.add_command(label="Pilih File (.mseed)", command=self.select_hvsr_files)
        self.HVSR_menu.add_command(label="Jalankan Proses HVSR", command=self.run_processing)
        self.HVSR_menu.add_separator()
        self.HVSR_menu.add_command(label="Simpan Gambar Hasil HVSR", command=self.save_figure)
        self.HVSR_menu.add_command(label="Simpan Hasil Analisis (.csv)", command=self.save_results)

        # Menu LFPS (placeholder)
        self.LFPS_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="LFPS", menu=self.LFPS_menu)

        # Menu EXIT
        exit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="EXIT", menu=exit_menu)
        exit_menu.add_command(label="Keluar dari Program", command=root.quit)

        # Frame utama
        main_frame = tk.Frame(root, padx=10, pady=20)
        main_frame.pack(fill='both', expand=True)

        # Judul dan deskripsi
        title = tk.Label(main_frame, text="Passive Seismic Data Processing Software", font=("Trebuchet", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 5))

        desc_text = (
            "Seismik pasif adalah salah satu metode geofisika yang memanfaat gelombang seismik bawah permukaann baik yang berasal dari tremor maupun dari mikroseismik. Pengukuran Pasif Seismik ini tidak membutuhkan artificial source, sehingga hanya mengandalkan sumber dari alam."
            "Software processing data pasif seismik ini dirancang untuk memudahkan geophysicist dalam melakukan pengolahan data pasif seismik mulai dari mergering data, trimming, bahkan processing. Software ini dilengkapi dengan fiture pengolahan data yang khusus mengarah pada metode HVSR dan LFPS. Semoga software ini memberikan sumbangsih kepada kemajuan ilmu pengetahuan dan teknologi khususnya di PT Geoservices."
        )
        desc_label = tk.Label(main_frame, text=desc_text, justify='justify', font=("Trebuchet", 10), wraplength=600)
        desc_label.grid(row=1, column=0, columnspan=2, sticky='w', pady=(0, 20))

        # Frame untuk gambar hasil (seismik penggabungan dan pemotongan)
        frame_gambar = tk.Frame(main_frame)
        frame_gambar.grid(row=2, column=0, sticky='ns')

        # Label dan gambar penggabungan di row 0 dan 1
        tk.Label(frame_gambar, text="Hasil Merger RAW Data", font=("Arial", 12, "underline")).grid(row=0, column=0, padx=20, pady=(0,5))
        self.label_img_gabung = tk.Label(frame_gambar, borderwidth=2, relief="groove")
        self.label_img_gabung.grid(row=1, column=0, padx=20, pady=10)

        # Label dan gambar pemotongan di row 2 dan 3
        tk.Label(frame_gambar, text="Hasil Trimming RAW Data", font=("Arial", 12, "underline")).grid(row=2, column=0, padx=20, pady=(10,5))
        self.label_img_potong = tk.Label(frame_gambar, borderwidth=2, relief="groove")
        self.label_img_potong.grid(row=3, column=0, padx=20, pady=10)

        # Frame gambar dan summary HVSR
        hvsr_frame = tk.Frame(main_frame)
        hvsr_frame.grid(row=2, column=1, sticky='ns')

        # Label gambar HVSR
        self.label_hvsr_title = tk.Label(hvsr_frame, text="Gambar Hasil Proses HVSR", font=("Arial", 12, "underline"))
        self.label_hvsr_title.pack(pady=(0,5))

        self.label_img_result = tk.Label(hvsr_frame, borderwidth=2, relief="groove")
        self.label_img_result.pack(pady=(0,10))

        # Text summary statistik HVSR
        self.text_summary = tk.Text(hvsr_frame, height=5, width=20, font=("Courier New", 10))
        self.text_summary.pack()

        # Status label
        self.status_label = tk.Label(main_frame, text="", font=("Arial", 10), fg="green")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=10)

    # ----- Fungsi untuk Seismic -----
    def pilih_dan_baca_files(self):
        file_paths = filedialog.askopenfilenames(title="Pilih file seismik",
                                                 filetypes=[("MiniSEED files", "*.mseed"), ("All files", "*.*")])
        if not file_paths:
            messagebox.showinfo("Info", "Tidak ada file yang dipilih.")
            return

        self.stream_gabungan = Stream()
        for file in file_paths:
            try:
                st = read(file)
                self.stream_gabungan += st
            except Exception as e:
                messagebox.showerror("Error", f"Gagal membaca file '{file}': {e}")

        messagebox.showinfo("Sukses", f"{len(file_paths)} file dibaca, total {len(self.stream_gabungan)} trace tergabung.")

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

        import tkinter.simpledialog as sd
        mulai_str = sd.askstring("Input Waktu Mulai", "Masukkan waktu mulai (YYYY-MM-DD HH:MM):")
        if not mulai_str:
            return
        selesai_str = sd.askstring("Input Waktu Selesai", "Masukkan waktu selesai (YYYY-MM-DD HH:MM):")
        if not selesai_str:
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

        self.stream_potongan = self.stream_gabungan.slice(starttime=mulai_waktu, endtime=selesai_waktu)

        if len(self.stream_potongan) == 0:
            messagebox.showinfo("Info", "Data pada interval waktu tersebut kosong.")
            return

        fig = self.stream_potongan.plot(show=False)
        path_potong = os.path.join(self.temp_dir, "gambar_potongan.png")
        fig.savefig(path_potong)
        plt.close(fig)
        self.tampilkan_gambar(path_potong, self.label_img_potong)

        messagebox.showinfo("Sukses", "Hasil plot pemotongan disimpan dan ditampilkan.")

    def simpan_data_gabungan(self):
        if len(self.stream_gabungan) == 0:
            messagebox.showwarning("Peringatan", "Belum ada data untuk disimpan.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".mseed",
                                            filetypes=[("MiniSEED files", "*.mseed"), ("All files", "*.*")],
                                            title="Simpan Data Gabungan Sebagai")
        if path:
            try:
                self.stream_gabungan.write(path, format="MSEED")
                messagebox.showinfo("Sukses", f"Data gabungan berhasil disimpan ke\n{path}")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal menyimpan data: {e}")

    def simpan_data_potongan(self):
        if not hasattr(self, 'stream_potongan') or len(self.stream_potongan) == 0:
            messagebox.showwarning("Peringatan", "Belum ada data potongan yang tersedia untuk disimpan.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".mseed",
                                            filetypes=[("MiniSEED files", "*.mseed"), ("All files", "*.*")],
                                            title="Simpan Data Potongan Sebagai")
        if path:
            try:
                self.stream_potongan.write(path, format="MSEED")
                messagebox.showinfo("Sukses", f"Data potongan berhasil disimpan ke\n{path}")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal menyimpan data: {e}")

    def tampilkan_gambar(self, path, label):
        image = Image.open(path)
        image = image.resize((300, 200))
        photo = ImageTk.PhotoImage(image)
        label.config(image=photo)
        label.image = photo

    # ----- Fungsi untuk HVSR -----
    def select_hvsr_files(self):
        files = filedialog.askopenfilenames(title="Pilih file MiniSEED untuk HVSR",
                                            filetypes=[("MiniSEED files", "*.mseed"), ("All files", "*.*")])
        if not files:
            self.status_label.config(text="Tidak ada file yang dipilih untuk HVSR.", fg="red")
            return
        self.fnames = [list(files)]
        missing_files = [f for fset in self.fnames for f in fset if not pathlib.Path(f).exists()]
        if missing_files:
            messagebox.showerror("Error", "File tidak ditemukan:\n" + "\n".join(missing_files))
            self.status_label.config(text="File tidak ditemukan untuk HVSR.", fg="red")
            return
        self.status_label.config(text=f"{sum(len(fset) for fset in self.fnames)} file HVSR berhasil dipilih.", fg="green")
        self.HVSR_menu.entryconfig("Jalankan Proses HVSR", state="normal")

    def run_processing(self):
        try:
            self.status_label.config(text="Memulai proses HVSR...", fg="blue")
            self.root.update_idletasks()

            preprocessing_settings = hvsrpy.settings.HvsrPreProcessingSettings()
            preprocessing_settings.detrend = "constant"
            preprocessing_settings.window_length_in_seconds = 30
            preprocessing_settings.orient_to_degrees_from_north = 0.0
            preprocessing_settings.filter_corner_frequencies_in_hz = (None, None)
            preprocessing_settings.ignore_dissimilar_time_step_warning = False

            processing_settings = hvsrpy.settings.HvsrTraditionalProcessingSettings()
            processing_settings.window_type_and_width = ("tukey", 0.01)
            processing_settings.smoothing = dict(operator="konno_and_ohmachi",
                                               bandwidth=40,
                                               center_frequencies_in_hz=np.geomspace(0.2, 50, 200))
            processing_settings.method_to_combine_horizontals = "geometric_mean"
            processing_settings.handle_dissimilar_time_steps_by = "frequency_domain_resampling"

            self.srecords = hvsrpy.read(self.fnames)
            self.srecords_preprocessed = hvsrpy.preprocess(self.srecords, preprocessing_settings)
            self.status_label.config(text="Preprocessing selesai...", fg="blue")
            self.root.update_idletasks()

            self.hvsr = hvsrpy.process(self.srecords_preprocessed, processing_settings)
            self.status_label.config(text="HVSR processing selesai...", fg="blue")
            self.root.update_idletasks()

            _ = hvsrpy.frequency_domain_window_rejection(self.hvsr, n=2, search_range_in_hz=(None, None))

            mfig, _ = hvsrpy.plot_pre_and_post_rejection(self.srecords_preprocessed, self.hvsr)
            self.tmp_result_path = os.path.join(self.temp_hvsr_dir, "result_processing.png")
            mfig.savefig(self.tmp_result_path)
            plt.close(mfig)

            self.tampilkan_gambar(self.tmp_result_path, self.label_img_result)

            teta = hvsrpy.summarize_hvsr_statistics(self.hvsr)
            summary_text = "-"*20 + "\nStatistical Summary:\n" + "-"*20 + "\n" + str(teta) + "\n"
            self.text_summary.config(state='normal')
            self.text_summary.delete(1.0, tk.END)
            self.text_summary.insert(tk.END, summary_text)
            self.text_summary.config(state='disabled')

            self.HVSR_menu.entryconfig("Simpan Gambar Hasil HVSR", state="normal")
            self.HVSR_menu.entryconfig("Simpan Hasil Analisis (.csv)", state="normal")
            self.status_label.config(text="Proses HVSR selesai. Anda dapat menyimpan hasil.", fg="green")
        except Exception as e:
            self.status_label.config(text="Proses HVSR gagal.", fg="red")
            messagebox.showerror("Error", f"Gagal menjalankan proses HVSR: {e}")

    def save_figure(self):
        fname = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")],
                                             title="Simpan Gambar Hasil HVSR")
        if fname:
            img = plt.imread(self.tmp_result_path)
            fig, ax = plt.subplots(figsize=(5,4))
            ax.imshow(img)
            ax.axis('off')
            fig.savefig(fname, dpi=300, bbox_inches='tight')
            plt.close(fig)
            messagebox.showinfo("Sukses", f"Gambar berhasil disimpan ke:\n{fname}")

    def save_results(self):
        if self.hvsr is None:
            self.status_label.config(text="Tidak ada hasil HVSR untuk disimpan.", fg="red")
            messagebox.showwarning("Peringatan", "Belum ada hasil analisis HVSR.")
            return
        fname = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")],
                                             title="Simpan Hasil Analisis HVSR")
        if fname:
            hvsrpy.object_io.write_hvsr_object_to_file(self.hvsr, fname)
            messagebox.showinfo("Sukses", f"Hasil analisis berhasil disimpan ke:\n{fname}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SeismicApp(root)
    root.mainloop()
