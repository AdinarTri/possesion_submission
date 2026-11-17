# Penanganan data

Dataset asli hanya dibaca. Repo ini tidak melakukan cleaning atau menulis ulang tracking, metadata, video, homography, maupun Smart Tagging. Keputusan berikut hanya berlaku pada inferensi turunan.

| Kondisi | Perilaku pipeline |
|---|---|
| Bola NaN/Inf | Tidak diimputasi. Tahan status maksimal 2 detik, lalu keluarkan X. |
| Koordinat pemain NaN/Inf atau di luar pitch | Tidak dipakai untuk kandidat jarak pada frame tersebut; nilai asli tidak diubah. |
| Satu tim tanpa posisi valid | Tidak mengasumsikan tim lain menguasai bola; diperlakukan sebagai observasi tidak lengkap. |
| Speed missing | Tidak memengaruhi jarak; speed tidak digunakan dalam model. Tidak ada konversi atau estimasi unit. |
| Bola di luar pitch | Bukti kandidat dead ball, perlu 13 frame berturut-turut; bukan koreksi posisi. |
| Track terfragmentasi/duplikat | Gunakan jarak minimum per tim. Tidak ada penggabungan identitas atau nomor punggung manual. |
| Tag bertumpuk dari tim sama | Satu dukungan boolean; tidak dihitung berkali-kali. |
| Tag bertentangan antartim atau Team N/A | Tidak memberikan veto khusus tim. |
| SET PIECES/GOALS | Tidak disalin menjadi D sepanjang interval. |
| Baris ATD salah, ID lompat, slot tidak sesuai | Gagal dengan error; tidak membuang, memotong, atau menambahkan baris diam-diam. |
| Jeda antar babak | Reset status memakai batas yang diterbitkan panitia, tanpa melihat video. |

Manifest mencatat hash sebelum/sesudah untuk ketiga input. File keluaran dan manifest tersimpan terpisah di artifacts/ dan tidak dimasukkan ke Git. Tidak ada export posisi mentah atau cuplikan video dalam repo submission.

X berarti abstain, bukan dead ball. D memerlukan bukti yang ditentukan algoritma. Tingkat missing, jumlah label dan jumlah keputusan merupakan diagnostik, bukan pengukuran akurasi. Konstanta tidak diubah berdasarkan statistik pertandingan ini.

Rencana cleaning lebih lanjut di folder kerja lama bukan bagian pipeline submission. Semua eksperimen manual/overlay lama tetap terpisah dan tidak digunakan untuk melatih, mengalibrasi atau memvalidasi metode ini.
