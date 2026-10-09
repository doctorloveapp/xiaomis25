"""Human-readable bindings: aliases are hidden, digit fields remain distinct."""
LABELS = {
    'timeHour': 'Ora completa (0–23)', 'timeMinute': 'Minuti completi (0–59)',
    'timeSecond': 'Secondi completi (0–59)', 'dateDay': 'Giorno del mese (1–31)',
    'timeHourLow': 'Cifra delle ore · unità', 'timeHourHigh': 'Cifra delle ore · decine',
    'timeMinuteLow': 'Cifra dei minuti · unità', 'timeMinuteHigh': 'Cifra dei minuti · decine',
    'timeSecondLow': 'Cifra dei secondi · unità', 'timeSecondHigh': 'Cifra dei secondi · decine',
    'dateDayLow': 'Cifra del giorno · unità', 'dateDayHigh': 'Cifra del giorno · decine',
}
DESCRIPTIONS = {
    'timeHour': 'L’ora intera in formato 24 ore. Alle 14:37 vale 14. Per un sottoquadrante delle ore, 24 valori e 720° corrispondono a due giri al giorno.',
    'timeMinute': 'I minuti interi dell’ora corrente, da 0 a 59. Alle 14:37 vale 37; intervallo 60 e rotazione 360° per un giro all’ora.',
    'timeSecond': 'I secondi interi, da 0 a 59. Intervallo 60 e rotazione 360° per un giro al minuto.',
    'timeHourLow': 'Solo la cifra delle unità dell’ora: alle 14:37 vale 4. Serve per indicatori della singola cifra, non per una lancetta oraria completa.',
    'timeHourHigh': 'Solo la cifra delle decine dell’ora: alle 14:37 vale 1. Può valere 0, 1 o 2.',
    'timeMinuteLow': 'Solo la cifra delle unità dei minuti: alle 14:37 vale 7 (da 0 a 9).',
    'timeMinuteHigh': 'Solo la cifra delle decine dei minuti: alle 14:37 vale 3 (da 0 a 5).',
    'timeSecondLow': 'Solo la cifra delle unità dei secondi, da 0 a 9.',
    'timeSecondHigh': 'Solo la cifra delle decine dei secondi, da 0 a 5.',
    'dateDayLow': 'Solo la cifra delle unità del giorno del mese: il giorno 27 vale 7.',
    'dateDayHigh': 'Solo la cifra delle decine del giorno del mese: il giorno 27 vale 2.',
    'systemSensorCompass': 'Direzione reale rilevata dalla bussola, in gradi: 0° nord, 90° est, 180° sud, 270° ovest. L’oggetto Bussola analogica ruota la rosa di −360° per mantenerla orientata al nord.',
    'systemStatusBattery': 'Carica residua dell’orologio, da 0 a 100%. Per una lancetta usa intervallo 100.',
    'healthHeartRate': 'Ultima frequenza cardiaca disponibile, in battiti al minuto; segue gli aggiornamenti del sensore dell’orologio.',
    'healthHeartRateMax': 'Frequenza cardiaca massima registrata, in battiti al minuto.',
    'healthHeartRateMin': 'Frequenza cardiaca minima registrata, in battiti al minuto.',
    'healthOxygenSpO2': 'Ultima saturazione di ossigeno disponibile, in percentuale.',
    'healthStepCount': 'Numero di passi della giornata.', 'healthStepTarget': 'Obiettivo giornaliero di passi impostato sull’orologio.',
    'healthStepKiloMeter': 'Distanza dei passi, in chilometri.',
    'healthCalorieValue': 'Calorie della giornata, in kcal.', 'healthCalorieTarget': 'Obiettivo giornaliero di calorie, in kcal.',
    'healthExerciseDuration': 'Durata del movimento registrata dall’orologio.',
    'healthStandCount': 'Numero di ore in cui l’orologio ha registrato attività in piedi.',
    'healthSleepDuration': 'Durata del sonno registrata dall’orologio.',
    'healthPressureIndex': 'Indice di stress registrato dall’orologio.',
    'systemSensorFusionAltitude': 'Altitudine stimata dai sensori dell’orologio, in metri.',
    'systemSensorAtmosphericPressure': 'Pressione rilevata dal barometro dell’orologio, in hPa.',
    'weatherCurrentWeather': 'Codice della condizione meteo sincronizzata dal telefono. Per una grafica usa le icone meteo delle complicazioni.',
    'weatherCurrentTemperature': 'Temperatura meteo corrente sincronizzata dal telefono, in °C; non misura la temperatura del corpo.',
    'weatherCurrentTemperatureFahrenheit': 'Temperatura meteo corrente sincronizzata dal telefono, in °F.',
    'weatherTodayTemperatureMax': 'Temperatura massima prevista per oggi, in °C.',
    'weatherTodayTemperatureMin': 'Temperatura minima prevista per oggi, in °C.',
    'weatherCurrentHumidity': 'Umidità meteo, in percentuale.', 'weatherCurrentWindLevel': 'Livello dell’intensità del vento fornito dal meteo.',
    'weatherCurrentWindDirection': 'Direzione del vento fornita dal meteo; distinta dal sensore bussola.',
    'weatherCurrentUVIndex': 'Indice UV fornito dal meteo.', 'weatherCurrentAirQualityIndex': 'Indice di qualità dell’aria fornito dal meteo.',
    'weatherCurrentPressure': 'Pressione atmosferica del servizio meteo; distinta dal barometro dell’orologio.',
    'dateMonth': 'Mese corrente: Dato live mostra il nome in inglese. La sorgente nativa resta numerica, da 1 a 12, per immagini e lancette.', 'dateDay': 'Giorno del mese, da 1 a 31.',
    'dateWeek': 'Dato live mostra MON, TUE, WED, THU, FRI, SAT o SUN; anteprima iniziale MON. La sorgente nativa resta numerica: 0=SUN, 1=MON, fino a 6=SAT.', 'dateYear': 'Anno corrente completo, per esempio 2026.',
    'systemStatusBluetooth': 'Stato della connessione Bluetooth dell’orologio; è un indicatore di stato, non una misura continua.',
    'miscIsPM': 'Indicatore della metà pomeridiana della giornata (PM).',
    'miscTimeSection': 'Fascia oraria nella codifica nativa dell’orologio.',
    'miscdateYestarday': 'Data del giorno precedente nella codifica nativa.',
    'miscdateTomorrow': 'Data del giorno successivo nella codifica nativa.',
    'dateMoon': 'Fase lunare nella codifica nativa dell’orologio.',
    'dateLunarDay': 'Giorno del calendario lunare.', 'dateLunarStringMonth': 'Mese lunare nella codifica nativa.',
    'dateLunarStringDay': 'Data lunare nella codifica nativa.',
}


def source_choices(sources):
    from .complications import ALIASES
    labels = {k: LABELS.get(k, v[0]) for k, v in sources.items() if k not in ALIASES}
    help_text = {}
    for key, label in labels.items():
        if key.endswith('Progress'):
            description = 'Progresso rispetto al relativo obiettivo giornaliero, espresso come percentuale nella sorgente nativa.'
        elif key.startswith('weatherCurrentSun'):
            description = ('Ore' if key.endswith('Hour') else 'Minuti') + ' dell’orario di ' + ('alba' if 'Rise' in key else 'tramonto') + ' previsto dal meteo.'
        else:
            description = 'Informazione nativa osservata nei quadranti forniti: ' + label + '.'
        help_text[key] = DESCRIPTIONS.get(key, description)
    return labels, help_text
