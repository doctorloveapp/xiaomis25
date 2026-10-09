# S5 Studio 1.7.4 — Set lancette

1. Avvia `S5Studio-1.7.4.exe` e apri **Set lancette**.
2. Cerca il nome oppure filtra per principali, piccole, personali/integrati o catalogo originale.
3. Premi **Modifica** sul set: importa/sostituisci PNG, clicca per il pivot, regola le ombre oppure usa **Genera ombre**. Anche i set originali sono modificabili; quelli AOD/incompleti mantengono i ruoli disponibili.
4. Premi **Aggiorna set nel catalogo**. Il salvataggio riguarda il catalogo: non modifica i livelli dei progetti già aperti/salvati.
5. Torna su **Quadrante**, scegli il modello e premi **Usa modello**. Per le principali la scelta delle ore abbina i ruoli del set e le ombre; per le piccole scegli la singola grafica.
6. **Ripristina** elimina la modifica locale e riprende il set incluso nell’EXE. **Elimina** nasconde un set personale/integrato soltanto nel catalogo locale, mantenendo autonomi i progetti.

## Distribuzione

Il solo EXE contiene i tre set Seiko/Swatch creati dall’utente: nove lancette, tredici PNG distinte. Mantiene anche i 595 modelli originali, ora accessibili al pannello di modifica. Non serve copiare AppData su un PC nuovo per ottenere questi tre set. Le modifiche locali hanno precedenza sulla versione incorporata, quindi un aggiornamento non sovrascrive i lavori personali sullo stesso PC.

Gli originali sono raggruppati usando gli ID effettivi degli abbinamenti, separando AOD e piccoli indicatori che possono riferirsi a un gruppo principale. L’editor copia la grafica nel deposito locale solo quando viene aperta per la modifica. I tre pivot esterni osservati sono mantenuti aggiungendo spazio trasparente, senza scalare o tagliare i pixel originali. Gli ID dei modelli rimangono stabili e gli abbinamenti continuano a funzionare dopo un salvataggio.

## Procedura per le prossime release

Eseguire `python -X utf8 scripts/sync_hand_sets.py` all’inizio di ogni modifica. Il packaging ripete automaticamente la procedura prima di raccogliere le risorse. Vengono letti `data/hand-sets/catalog.json` e `%LOCALAPPDATA%/S5Studio/hand-sets/catalog.json`; quest’ultimo prevale per ID coincidenti. Il catalogo distribuibile è `resources/hand-sets/catalog.json`, con PNG identificate dal loro SHA256. Le sorgenti non vengono modificate; i default già integrati restano disponibili anche se un catalogo locale è assente. L’operazione è ripetibile e incorpora nuovi set e revisioni dei set esistenti. Una PNG mancante/alterata blocca il rilascio.

I file di `resources/hand-sets/` sono inclusi nel repository, senza modificare `.gitignore`, e nel manifesto verificato staticamente dentro l’EXE. Il rapporto `hand-set-integration-1.7.4.json` registra i cataloghi controllati e i set distribuiti. Restano invariati runtime Lua, comportamento Crono/Pro e geometria dei livelli già salvati.
