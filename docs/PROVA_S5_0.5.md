# Prova del nuovo analogico 0.5

Apri **S5Studio-0.5.exe**. Per modificare il test già pronto usa Apri e scegli `projects/S5_Analogico_Libero_0.5.s5faceproj`; poi Esporta ZIP. Per la prima prova puoi utilizzare direttamente `S5_Analogico_Libero_0.5_TEMPLATE.zip` nella root.

1. Copia il nuovo ZIP sul telefono **senza estrarlo**. Mantieni S5 connesso e sincronizzato.
2. Apri Local watchfaces uploader nella mod. Se il controllo capabilities fallisce, usa Verify capability test disattivato, come nelle tue installazioni riuscite, quindi seleziona il nuovo ZIP e installa.
3. Controlla l’anteprima dall’orologio e dal pulsante Modifica. Deve mostrare “S5 LIBERO” con cinque caselle, senza la grafica Suit and tie. La lista locale della mod potrebbe ancora non mostrare l’immagine: anche il riferimento originale presenta quel comportamento.
4. Seleziona Menta, Azzurro, Arancio, Viola e Bianco. Colore di lancette, tacche e caselle deve cambiare. Prova ogni slot separatamente: scegli ad esempio Batteria al posto di Passi, SpO₂ al posto di Pulsazioni e Nessuna al posto di Meteo. Verifica che cambino solo le caselle selezionate e che le scelte restino dopo aver riaperto Modifica.
5. Confronta i dati con le schermate di sistema; sincronizza il meteo e verifica bussola/calibrazione, ore/minuti/secondi, spegnimento/risveglio e AOD. In AOD vedrai lancette/data essenziali, senza le cinque caselle.

Il progetto pronto ha cinque slot iniziali: Passi, Pulsazioni, Temperatura, Bussola e Meteo. Ogni slot offre 15 opzioni. Nell’editor puoi aggiungere altri slot fino alla guardia applicativa di 16 e selezionare tutte le 58 sorgenti osservate.

Questa è una nuova prova hardware: il pacchetto è compilato e controllato sul PC, non ancora collaudato sul tuo S5. Annota lo ZIP preciso usato, l’esito di ciascun punto e una foto se il risultato differisce dall’anteprima. Il report e gli hash della build sono in `docs/S5-Analogico-Libero-0.5-build-report.json`.
