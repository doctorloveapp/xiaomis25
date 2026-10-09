# S5 Studio — preferenze di lavoro dell'utente

- A ogni nuova modifica controllare i set personali con `python -X utf8 scripts/sync_hand_sets.py`. Integrare i nuovi set e gli aggiornamenti in `resources/hand-sets/`, mantenendo intatti i cataloghi sorgente. Il packaging ripete automaticamente questo controllo.
- Aggiornare README e documenti pertinenti e produrre l'eseguibile della versione richiesta, dopo i soli controlli necessari.
- Non creare backup di regressione, non avviare l'eseguibile in ambienti isolati e non generare quadranti ZIP dimostrativi salvo necessità concreta. Sono consentiti test sui sorgenti e verifica statica del bundle.
- Conservare gli elementi del `.gitignore` personalizzati dall'utente.
