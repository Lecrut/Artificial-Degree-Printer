## Najnowsze prace, analiza porównawcza i luka badawcza
### 2.2 Najnowsze prace, analiza porównawcza i luka badawcza

W kontekście detekcji anomalii w danych wielokanałowych, zwłaszcza w obszarze sygnalizacji telemetrii, ostatnie opracowania koncentrują się na integracji głębokiego uczenia z protokołami stres-testów oraz podejścią ensemblistyczną do zapewnienia niezawodności.

Pierwszą kluczową pracą jest Rad et al. [rad2017deep], która proponuje zastosowanie sieci głębokich do automatycznego wykrywania SMM (Single Measurement Mode) wykorzystując wielosiłowe IMU. Choć badania skupiają się na danych z akcelerometrów, koncepcja wdrażania detektorów opartych na cechach wieloosowych i ich synergii stanowi bezpośredni precedent dla propozycji ensembli opartych na feature engineeringu w tej pracy. Artykuł ten służy jako punkt odniesienia dla architektury przetwarzających równoległe strumienie informacji, co jest krytyczne przy analizie sygnałów biofizycznych o strukturze wielokanałowej.

Drugi istotny wkład stanowi Mohammed et al. [mohammad2026sift] z protokołem FaithShift i metodą SIFT (Stress-Informed Feature Trajectory). Praca ta wprowadza mechanizm testu krytycznego obejmujący dziesięć osi przesunięć (shift axes) oraz celu uczenia się o niezmienniczności w skrajnych środowiskach. To podejście jest fundamentalne do zrozumienia ograniczeń statystycznych bazelines typu Z-score, które często zawodzą przy dużych przesunięciach rozkładu lub nietypowych zdarzeniach (np. spikes, drift). Metodologia SIFT operuje na trajektorii ukrytego stanu i wrażliwości cechy na różne perturbacje, co bezpośrednio wskazuje na potrzebę dynamicznej oceny anomalií, a nie jedynie punktowej analizy statystycznej.

Obydwa źródła [rad2017deep], [mohammad2026sift] potwierdzają istniejące ograniczenia tradycyjnych metod uniwariacyjnych (np. Z-score) w detekcji anomalii o rzadkim występowaniu i nieprzewidywalnym charakterze. Ich analiza porównawcza opiera się na precyzji wykrywania oraz stabilności na danych z różnych środowisk operacyjnych, co wskazuje na lukę, którą wypełnia proponowany eksperyment wieloetapowy.

**Komunikaty bazylkowe:**
- Robust PCA / Deep features (rad2017deep)
- Trajectory-based anomaly detection (mohammad2026sift)

**Luka badawcza:**
Brak badań nad tym, czy ensemblista detektor oparty na wielocech (synetyczne sygnały ECG/EEG) może przekroczyć w statystyce niezawodności (F1-score, delay, stabilność) prostą bazylę Z-score przy testach stresowych i niestandardowych anomalii. Oczekiwany rezultat: weryfikacja przewagi dynamicznych ensembli nad statystyczną rzepią w warunkach real-time.
