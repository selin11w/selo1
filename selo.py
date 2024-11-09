import pulp
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Parametreler
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
shifts = ['Morning', 'Mid-day', 'Night']

# Vardiya başına saatler (örnek olarak)
shift_hours = {'Morning': 8, 'Mid-day': 8, 'Night': 8}

# Minimum ve Maksimum Gereksinimler
min_waiters = {'Morning': 2, 'Mid-day': 3, 'Night': 3}
max_waiters = {'Morning': 3, 'Mid-day': 4, 'Night': 5}

min_chefs = {'Morning': 1, 'Mid-day': 2, 'Night': 2}
max_chefs = {'Morning': 1, 'Mid-day': 3, 'Night': 3}

# Parametrelerin tanımı
num_waiters = 18  # Garson sayısı
num_chefs = 10  # Şef sayısı
total_staff = num_waiters + num_chefs  # Toplam personel sayısı

# Problem Tanımı
model = pulp.LpProblem("Staff_Scheduling", pulp.LpMinimize)

# Karar Değişkenleri: Personelin vardiyaya atanıp atanmadığını gösterir (0 veya 1)
x = pulp.LpVariable.dicts('x', (range(total_staff), range(7), range(3)), 0, 1, pulp.LpBinary)

# Amaç fonksiyonu: Sapmaların toplamını minimize et
d_n = pulp.LpVariable.dicts('d_n', range(total_staff), lowBound=0, cat='Continuous')
d_p = pulp.LpVariable.dicts('d_p', range(total_staff), lowBound=0, cat='Continuous')
model += pulp.lpSum(d_n[i] + d_p[i] for i in range(total_staff))

# Kısıtlar

# 1. Garsonlar için vardiya başına minimum ve maksimum sayılar
for j in range(7):  # Günler
    # Sabah vardiyasında gerekli garson sayısı
    model += pulp.lpSum(x[i][j][0] for i in range(num_waiters)) >= min_waiters['Morning']
    model += pulp.lpSum(x[i][j][0] for i in range(num_waiters)) <= max_waiters['Morning']

    # Öğlen vardiyasında gerekli garson sayısı
    model += pulp.lpSum(x[i][j][1] for i in range(num_waiters)) >= min_waiters['Mid-day']
    model += pulp.lpSum(x[i][j][1] for i in range(num_waiters)) <= max_waiters['Mid-day']

    # Gece vardiyasında gerekli garson sayısı
    model += pulp.lpSum(x[i][j][2] for i in range(num_waiters)) >= min_waiters['Night']
    model += pulp.lpSum(x[i][j][2] for i in range(num_waiters)) <= max_waiters['Night']

# Garsonların haftada bir gün izinli olup altı gün çalışması
for i in range(num_waiters):
    model += pulp.lpSum(x[i][j][k] for j in range(7) for k in range(3)) == 6

# Garsonların hafta sonu çalışma zorunluluğu
for j in [5, 6]:  # Cumartesi ve Pazar
    model += pulp.lpSum(x[i][j][k] for i in range(num_waiters) for k in range(3)) == num_waiters

# Garsonlar günlük tek vardiyaya atanmalı
for i in range(num_waiters):
    for j in range(7):
        model += pulp.lpSum(x[i][j][k] for k in range(3)) <= 1

# Gece vardiyasına atanan bir garsonun ertesi sabah vardiyasına atanamama kısıtı
for i in range(num_waiters):
    for j in range(6):  # Son gün dışındaki günler için
        model += x[i][j][2] + x[i][j + 1][0] <= 1

# 2. Şefler için vardiya başına minimum ve maksimum sayılar
for j in range(7):
    # Sabah vardiyasında gerekli şef sayısı
    model += pulp.lpSum(x[i][j][0] for i in range(num_waiters, total_staff)) == min_chefs['Morning']

    # Öğlen vardiyasında gerekli şef sayısı
    model += pulp.lpSum(x[i][j][1] for i in range(num_waiters, total_staff)) >= min_chefs['Mid-day']
    model += pulp.lpSum(x[i][j][1] for i in range(num_waiters, total_staff)) <= max_chefs['Mid-day']

    # Gece vardiyasında gerekli şef sayısı
    model += pulp.lpSum(x[i][j][2] for i in range(num_waiters, total_staff)) >= min_chefs['Night']
    model += pulp.lpSum(x[i][j][2] for i in range(num_waiters, total_staff)) <= max_chefs['Night']

# Şeflerin haftada bir kez sabah vardiyasına atanma kısıtı
for i in range(num_waiters, total_staff):
    model += pulp.lpSum(x[i][j][0] for j in range(7)) <= 1

# Şeflerin haftada bir gün izinli olup altı gün çalışması
for i in range(num_waiters, total_staff):
    model += pulp.lpSum(x[i][j][k] for j in range(7) for k in range(3)) == 6

# Şeflerin hafta sonu çalışma zorunluluğu
for j in [5, 6]:  # Cumartesi ve Pazar
    model += pulp.lpSum(x[i][j][k] for i in range(num_waiters, total_staff) for k in range(3)) == num_chefs

# Şefler günlük tek vardiyaya atanmalı
for i in range(num_waiters, total_staff):
    for j in range(7):
        model += pulp.lpSum(x[i][j][k] for k in range(3)) <= 1

# Gece vardiyasına atanan bir şefin ertesi sabah vardiyasına atanamama kısıtı
for i in range(num_waiters, total_staff):
    for j in range(6):
        model += x[i][j][2] + x[i][j + 1][0] <= 1

# Modeli çöz
model.solve()

# Sonuçları sözlüklere aktar
waiter_schedule = {day: {shift: [] for shift in shifts} for day in days}
chef_schedule = {day: {shift: [] for shift in shifts} for day in days}

for i in range(num_waiters):
    for j in range(7):
        for k in range(3):
            if pulp.value(x[i][j][k]) == 1:
                waiter_schedule[days[j]][shifts[k]].append(f"W{i + 1}")

for i in range(num_waiters, total_staff):
    for j in range(7):
        for k in range(3):
            if pulp.value(x[i][j][k]) == 1:
                chef_schedule[days[j]][shifts[k]].append(f"C{i + 1}")

# DataFrame oluşturma
waiter_df = pd.DataFrame(waiter_schedule)
chef_df = pd.DataFrame(chef_schedule)

# İzin günlerini liste halinde çıkartalım
waiter_days_off = {f"W{i + 1}": [days[j] for j in range(7) if all(pulp.value(x[i][j][k]) == 0 for k in range(3))] for i in range(num_waiters)}
chef_days_off = {f"C{i + 1}": [days[j] for j in range(7) if all(pulp.value(x[i][j][k]) == 0 for k in range(3))] for i in range(num_waiters, total_staff)}

# DataFrame oluşturma - Her çalışanın izin günleri bir listede olacak şekilde
waiter_off_df = pd.DataFrame(list(waiter_days_off.items()), columns=["Waiter", "Days Off"])
chef_off_df = pd.DataFrame(list(chef_days_off.items()), columns=["Chef", "Days Off"])

# Streamlit App
st.title("Shift Scheduling Optimization Results")

# Waiter tablosunu görüntüle
st.subheader("Table 2: Shift Schedule for Waiters")
st.dataframe(waiter_df)

# Chef tablosunu görüntüle
st.subheader("Table 3: Shift Schedule for Chefs")
st.dataframe(chef_df)

# Streamlit'te gösterme
st.subheader("Table 4: Days Off for Waiters")
st.dataframe(waiter_off_df)

st.subheader("Table 5: Days Off for Chefs")
st.dataframe(chef_off_df)

# Streamlit App
st.title("Shift Scheduling Optimization Results")

# Waiter tablosunu görüntüle
st.subheader("Table 2: Shift Schedule for Waiters")
st.dataframe(waiter_df)

# Chef tablosunu görüntüle
st.subheader("Table 3: Shift Schedule for Chefs")
st.dataframe(chef_df)


# Vardiya kapsamını görselleştir
st.subheader("Shift Coverage Analysis")

chef_counts = {day: {shift: len(chef_schedule[day][shift]) for shift in shifts} for day in days}
waiter_counts = {day: {shift: len(waiter_schedule[day][shift]) for shift in shifts} for day in days}

chef_counts_df = pd.DataFrame(chef_counts).T
waiter_counts_df = pd.DataFrame(waiter_counts).T

# chef vardiya kapsamı grafiği
st.write("chef Shift Coverage")
fig1, ax1 = plt.subplots(figsize=(10, 6))
chef_counts_df.plot(kind="bar", stacked=True, ax=ax1)
plt.title("chef Shift Coverage by Day and Shift")
plt.xlabel("Day")
plt.ylabel("Number of chef")
st.pyplot(fig1)

# waiter vardiya kapsamı grafiği
st.write("Waiter Shift Coverage")
fig2, ax2 = plt.subplots(figsize=(10, 6))
waiter_counts_df.plot(kind="bar", stacked=True, ax=ax2)
plt.title("Waiter Shift Coverage by Day and Shift")
plt.xlabel("Day")
plt.ylabel("Number of Waiters")
st.pyplot(fig2)
