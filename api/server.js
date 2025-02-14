const express = require('express');
const app = express();

const PORT = process.env.PORT;

app.use(express.json());

app.get('/api/v1/health', (req, res) => {
    res.json({ status: 'ok' });
});

app.use((req, res, next) => {
    res.status(404).json({ error: 'Not found' });
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
