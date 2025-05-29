# Finger Drawing Application

An interactive application that allows you to draw on your webcam feed using your finger. The app tracks your index finger and enables drawing when your finger tip is positioned above your finger base. If your drawings end up in front of your face, they will automatically follow your face movements.

## Features

-   Hand tracking to detect finger positions
-   Drawing is enabled when your finger tip is above its base
-   Face detection
-   Drawings near your face will move with your face
-   Interactive canvas with real-time feedback

## Requirements

-   Python 3.8 or higher
-   OpenCV
-   MediaPipe
-   NumPy

## Installation

1. Clone this repository
2. Install the required dependencies:
    ```
    pip install -r requirements.txt
    ```

## Usage

Run the main script:

```
python main.py
```

### Controls:

-   Position your index finger tip above its base to start drawing
-   Lower your finger tip below its base to stop drawing
-   Press 'q' to quit the application

## How It Works

The application uses:

-   MediaPipe's Hand Landmarks model to track your finger positions
-   MediaPipe's Face Detection model to detect and track your face
-   OpenCV for image processing and visualization
-   A custom drawing canvas that updates in real-time

## 👨‍💻 Anggota Kelompok

| Nama Lengkap        | NIM       | GitHub ID |
| ------------------- | --------- | --------- |
| Joshua Palti Sinaga | 122140141 | @jo0707   |

---

## 📘 Logbook Mingguan

### Week 1 (5 - 11 Mei 2025)

- Pembuatan Repository

### Week 2 (12 - 18 Mei 2025)

- Implementasi pelacakan tangan menggunakan MediaPipe
- Implementasi fitur gambar mengikuti gerakan wajah
- Mekanisme menggambar dengan jari telunjuk
- UI untuk reset, save, pemilihan warna, ukuran kuas
- File konfigurasi untuk aplikasi

### Week 3 (19 - 25 Mei 2025)

TODO
- Implementasi Optical Flow Lucas-Kanade untuk pelacakan jari
- sfx untuk menggambar dan tombol


### Week 4 (26 - 30 Mei 2025)

- Fitur save menyimpan kamera dan gambar

## 📚 Referensi
