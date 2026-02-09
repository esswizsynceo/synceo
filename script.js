// --- PARTIE 1 : Charger le hash depuis le fichier texte ---
async function loadSHA() {
    try {
        // On récupère le fichier (remplacez par le bon chemin si nécessaire)
        const response = await fetch('sha256.txt?v=' + Date.now());
        if (!response.ok) throw new Error('Fichier sha256 introuvable');
        
        const shaText = await response.text();
        
        // On affiche le texte dans la balise span
        document.getElementById('sha-value').innerText = shaText.trim();
    } catch (error) {
        console.error('Erreur:', error);
        document.getElementById('sha-value').innerText = "Erreur de chargement";
    }
}

// Lancer le chargement dès que la page est prête
window.onload = loadSHA;

// --- PARTIE 2 : La fonction de copie (inchangée) ---
function copySHA() {
    // 1. Récupérer le texte du SHA
    const shaText = document.getElementById('sha-value').innerText;
    const btn = document.getElementById('copy-btn');

    // 2. Utiliser l'API Clipboard
    navigator.clipboard.writeText(shaText).then(() => {
        // 3. Petit bonus : changer le texte du bouton pour confirmer
        btn.innerText = "Copié !";
        btn.style.backgroundColor = "#4CAF50"; // Vert
        btn.style.color = "white";

        // Revenir à l'état initial après 2 secondes
        setTimeout(() => {
            btn.innerText = "Copier";
            btn.style.backgroundColor = "";
            btn.style.color = "";
        }, 2000);
    }).catch(err => {
        console.error('Erreur lors de la copie : ', err);
    });
}

