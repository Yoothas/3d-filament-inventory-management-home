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

// AMS Integration API Endpoints

// Reduce filament usage after print completion
app.post('/api/filaments/:id/use', (req, res) => {
    const filaments = readFilaments();
    const filamentIndex = filaments.findIndex(f => f.id === req.params.id);
    
    if (filamentIndex === -1) {
        return res.status(404).json({ error: 'Filament not found' });
    }
    
    const usedWeight = parseFloat(req.body.usedWeight);
    const printJob = req.body.printJob || 'Unknown';
    const printTime = req.body.printTime || 0;
    
    if (isNaN(usedWeight) || usedWeight <= 0) {
        return res.status(400).json({ error: 'Invalid used weight' });
    }
    
    const filament = filaments[filamentIndex];
    const newRemainingWeight = Math.max(0, filament.remainingWeight - usedWeight);
    
    // Update filament
    const updatedFilament = {
        ...filament,
        remainingWeight: newRemainingWeight,
        lastUsed: new Date().toISOString(),
        printHistory: [
            ...(filament.printHistory || []),
            {
                date: new Date().toISOString(),
                usedWeight,
                printJob,
                printTime,
                remainingAfter: newRemainingWeight
            }
        ].slice(-10) // Keep last 10 print jobs
    };
    
    filaments[filamentIndex] = updatedFilament;
    
    if (writeFilaments(filaments)) {
        res.json({
            success: true,
            filament: updatedFilament,
            message: `Used ${usedWeight}g of ${filament.brand} ${filament.color}. ${newRemainingWeight}g remaining.`
        });
    } else {
        res.status(500).json({ error: 'Failed to update filament usage' });
    }
});

// Search filaments for AMS auto-detection
app.get('/api/filaments/search', (req, res) => {
    const filaments = readFilaments();
    const { material, color, brand, ams_slot } = req.query;
    
    let filtered = filaments.filter(f => f.remainingWeight > 0); // Only available spools
    
    if (material) {
        filtered = filtered.filter(f => 
            f.material.toLowerCase().includes(material.toLowerCase())
        );
    }
    
    if (color) {
        filtered = filtered.filter(f => 
            f.color.toLowerCase().includes(color.toLowerCase())
        );
    }
    
    if (brand) {
        filtered = filtered.filter(f => 
            f.brand.toLowerCase().includes(brand.toLowerCase())
        );
    }
    
    // Sort by remaining weight (most full first)
    filtered.sort((a, b) => b.remainingWeight - a.remainingWeight);
    
    res.json({
        matches: filtered,
        count: filtered.length,
        query: { material, color, brand, ams_slot }
    });
});

// Bulk usage for multi-material prints
app.post('/api/filaments/bulk-use', (req, res) => {
    const usageData = req.body;
    const filaments = readFilaments();
    const results = [];
    
    if (!Array.isArray(usageData)) {
        return res.status(400).json({ error: 'Expected array of usage data' });
    }
    
    for (const usage of usageData) {
        const filamentIndex = filaments.findIndex(f => f.id === usage.id);
        
        if (filamentIndex === -1) {
            results.push({ id: usage.id, error: 'Filament not found' });
            continue;
        }
        
        const usedWeight = parseFloat(usage.usedWeight);
        if (isNaN(usedWeight) || usedWeight <= 0) {
            results.push({ id: usage.id, error: 'Invalid used weight' });
            continue;
        }
        
        const filament = filaments[filamentIndex];
        const newRemainingWeight = Math.max(0, filament.remainingWeight - usedWeight);
        
        filaments[filamentIndex] = {
            ...filament,
            remainingWeight: newRemainingWeight,
            lastUsed: new Date().toISOString(),
            printHistory: [
                ...(filament.printHistory || []),
                {
                    date: new Date().toISOString(),
                    usedWeight,
                    printJob: usage.printJob || 'Multi-material print',
                    printTime: usage.printTime || 0,
                    remainingAfter: newRemainingWeight
                }
            ].slice(-10)
        };
        
        results.push({
            id: usage.id,
            success: true,
            usedWeight,
            remainingWeight: newRemainingWeight,
            filament: `${filament.brand} ${filament.color}`
        });
    }
    
    if (writeFilaments(filaments)) {
        res.json({ results, timestamp: new Date().toISOString() });
    } else {
        res.status(500).json({ error: 'Failed to save filament updates' });
    }
});

// AMS status endpoint for mapping physical slots to inventory
app.get('/api/ams/status', (req, res) => {
    // This would eventually integrate with actual AMS data
    // For now, return a template for manual mapping
    const amsSlots = {
        slot_1: { filament_id: null, material: null, color: null },
        slot_2: { filament_id: null, material: null, color: null },
        slot_3: { filament_id: null, material: null, color: null },
        slot_4: { filament_id: null, material: null, color: null }
    };
    
    res.json({
        ams_slots: amsSlots,
        message: 'AMS integration ready - map filaments to slots in your slicer'
    });
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