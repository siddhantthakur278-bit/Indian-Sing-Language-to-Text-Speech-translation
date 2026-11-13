// Unit test verifying normalize implementation against ml/sample_io.json
const fs = require('fs');
const path = require('path');

function normalize(sequence) {
  return sequence.map((frame) => {
    const normalizedFrame = [...frame];

    const lsX = frame[44];
    const lsY = frame[45];
    const lsZ = frame[46];

    const rsX = frame[48];
    const rsY = frame[49];
    const rsZ = frame[50];

    const centerX = (lsX + rsX) / 2.0;
    const centerY = (lsY + rsY) / 2.0;
    const centerZ = (lsZ + rsZ) / 2.0;

    const dx = lsX - rsX;
    const dy = lsY - rsY;
    const dz = lsZ - rsZ;
    const scale = Math.sqrt(dx * dx + dy * dy + dz * dz) + 1e-6;

    for (let i = 0; i < 33; i++) {
      const idx = i * 4;
      normalizedFrame[idx] = (frame[idx] - centerX) / scale;
      normalizedFrame[idx + 1] = (frame[idx + 1] - centerY) / scale;
      normalizedFrame[idx + 2] = (frame[idx + 2] - centerZ) / scale;
    }

    for (let i = 0; i < 21; i++) {
      const idx = 132 + i * 3;
      const hx = frame[idx];
      const hy = frame[idx + 1];
      const hz = frame[idx + 2];
      if (Math.abs(hx) > 1e-5 || Math.abs(hy) > 1e-5 || Math.abs(hz) > 1e-5) {
        normalizedFrame[idx] = (hx - centerX) / scale;
        normalizedFrame[idx + 1] = (hy - centerY) / scale;
        normalizedFrame[idx + 2] = (hz - centerZ) / scale;
      } else {
        normalizedFrame[idx] = 0.0;
        normalizedFrame[idx + 1] = 0.0;
        normalizedFrame[idx + 2] = 0.0;
      }
    }

    for (let i = 0; i < 21; i++) {
      const idx = 195 + i * 3;
      const hx = frame[idx];
      const hy = frame[idx + 1];
      const hz = frame[idx + 2];
      if (Math.abs(hx) > 1e-5 || Math.abs(hy) > 1e-5 || Math.abs(hz) > 1e-5) {
        normalizedFrame[idx] = (hx - centerX) / scale;
        normalizedFrame[idx + 1] = (hy - centerY) / scale;
        normalizedFrame[idx + 2] = (hz - centerZ) / scale;
      } else {
        normalizedFrame[idx] = 0.0;
        normalizedFrame[idx + 1] = 0.0;
        normalizedFrame[idx + 2] = 0.0;
      }
    }

    return normalizedFrame;
  });
}

const sampleIoPath = path.resolve(__dirname, '../ml/sample_io.json');
if (!fs.existsSync(sampleIoPath)) {
  console.error('sample_io.json not found at ' + sampleIoPath);
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(sampleIoPath, 'utf8'));
const rawSequences = data.raw;
const expectedNorm = data.normalized;

let maxDiff = 0.0;
const tolerance = 1e-4;

for (let s = 0; s < rawSequences.length; s++) {
  const actualNorm = normalize(rawSequences[s]);
  const expected = expectedNorm[s];

  for (let f = 0; f < actualNorm.length; f++) {
    for (let c = 0; c < actualNorm[f].length; c++) {
      const diff = Math.abs(actualNorm[f][c] - expected[f][c]);
      if (diff > maxDiff) maxDiff = diff;
      if (diff > tolerance) {
        console.error(`Mismatch at seq ${s}, frame ${f}, col ${c}: actual=${actualNorm[f][c]}, expected=${expected[f][c]}, diff=${diff}`);
        process.exit(1);
      }
    }
  }
}

console.log(`Unit Test Passed! Max difference: ${maxDiff.toExponential(4)} (well below tolerance ${tolerance})`);
