const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;
const DATA_FILE = path.join(__dirname, 'data', 'filaments.json');

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// Ensure data directory exists
const dataDir = path.join(__dirname, 'data');
if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir);
}

// Initialize data file if it doesn't exist
if (!fs.existsSync(DATA_FILE)) {
    const initialData = [];
    fs.writeFileSync(DATA_FILE, JSON.stringify(initialData, null, 2));
}

// Helper function to read filaments
function readFilaments() {
    try {
        const data = fs.readFileSync(DATA_FILE, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        console.error('Error reading filaments:', error);
        return [];
    }
}

// Helper function to write filaments
function writeFilaments(filaments) {
    try {
        fs.writeFileSync(DATA_FILE, JSON.stringify(filaments, null, 2));
        return true;
    } catch (error) {
        console.error('Error writing filaments:', error);
        return false;
    }
}

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API Routes
app.get('/api/filaments', (req, res) => {
    const filaments = readFilaments();
    res.json(filaments);
});

app.post('/api/filaments', (req, res) => {
    const filaments = readFilaments();
    const newFilament = {
        id: Date.now().toString(),
        brand: req.body.brand,
        material: req.body.material,
        color: req.body.color,
        weight: parseFloat(req.body.weight),
        remainingWeight: parseFloat(req.body.weight),
        diameter: parseFloat(req.body.diameter),
        purchaseDate: req.body.purchaseDate,
        cost: parseFloat(req.body.cost) || 0,
        notes: req.body.notes || '',
        createdAt: new Date().toISOString()
    };
    
    filaments.push(newFilament);
    
    if (writeFilaments(filaments)) {
        res.json(newFilament);
    } else {
        res.status(500).json({ error: 'Failed to save filament' });
    }
});

app.put('/api/filaments/:id', (req, res) => {
    const filaments = readFilaments();
    const filamentIndex = filaments.findIndex(f => f.id === req.params.id);
    
    if (filamentIndex === -1) {
        return res.status(404).json({ error: 'Filament not found' });
    }
    
    const updatedFilament = {
        ...filaments[filamentIndex],
        brand: req.body.brand,
        material: req.body.material,
        color: req.body.color,
        weight: parseFloat(req.body.weight),
        remainingWeight: parseFloat(req.body.remainingWeight),
        diameter: parseFloat(req.body.diameter),
        purchaseDate: req.body.purchaseDate,
        cost: parseFloat(req.body.cost) || 0,
        notes: req.body.notes || '',
        updatedAt: new Date().toISOString()
    };
    
    filaments[filamentIndex] = updatedFilament;
    
    if (writeFilaments(filaments)) {
        res.json(updatedFilament);
    } else {
        res.status(500).json({ error: 'Failed to update filament' });
    }
});

app.delete('/api/filaments/:id', (req, res) => {
    const filaments = readFilaments();
    const filamentIndex = filaments.findIndex(f => f.id === req.params.id);
    
    if (filamentIndex === -1) {
        return res.status(404).json({ error: 'Filament not found' });
    }
    
    filaments.splice(filamentIndex, 1);
    
    if (writeFilaments(filaments)) {
        res.json({ message: 'Filament deleted successfully' });
    } else {
        res.status(500).json({ error: 'Failed to delete filament' });
    }
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`3D Filament Inventory Server running on port ${PORT}`);
    console.log(`Access the application at:`);
    console.log(`  Local: http://localhost:${PORT}`);
    console.log(`  Network: http://YOUR_IP_ADDRESS:${PORT}`);
    console.log(`\nShare the Network URL with your roommate to access from their browser!`);
});

module.exports = app;