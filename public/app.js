/**
 * CardioPredict AI - Frontend Logic & Dual Inference Engine
 * Provides reactive UI bindings, presets, SVG gauge animation, and seamless API + client-side inference.
 */

// Offline/Client-side exact model parameters matching trained pipeline
const CLIENT_MODEL = {
  features: [
    "age", "blood_pressure", "cholesterol", "bmi", "physical_activity", "stress_level",
    "sex_Male", "smoker_Yes", "diabetes_Yes", "family_history_Yes"
  ],
  means: [55.4675, 132.8825, 220.97, 29.045, 2.0175, 4.9025],
  scales: [14.3181, 26.8096, 43.9665, 6.3731, 1.4026, 2.5996],
  intercept: 0.03018,
  coefficients: [
    -0.0578, // age
    -0.1027, // blood_pressure
    -0.0312, // cholesterol
    0.0191,  // bmi
    0.0249,  // physical_activity
    -0.0366, // stress_level
    0.0362,  // sex_Male (One-Hot Encoded)
    0.3541,  // smoker_Yes (One-Hot Encoded, primary statistical driver)
    -0.0221, // diabetes_Yes (One-Hot Encoded)
    -0.0185  // family_history_Yes (One-Hot Encoded)
  ]
};

// Preset Profiles
const PRESETS = {
  healthy: {
    age: 36, sex: "Female", blood_pressure: 105, cholesterol: 175,
    bmi: 22.4, smoker: "No", diabetes: "No", physical_activity: 4, family_history: "No", stress_level: 2
  },
  borderline: {
    age: 56, sex: "Male", blood_pressure: 135, cholesterol: 215,
    bmi: 27.8, smoker: "No", diabetes: "No", physical_activity: 2, family_history: "Yes", stress_level: 5
  },
  highrisk: {
    age: 68, sex: "Male", blood_pressure: 165, cholesterol: 270,
    bmi: 33.5, smoker: "Yes", diabetes: "Yes", physical_activity: 0, family_history: "Yes", stress_level: 8
  }
};

document.addEventListener("DOMContentLoaded", () => {
  // UI Element References
  const form = document.getElementById("prediction-form");
  const ageInput = document.getElementById("age");
  const bpInput = document.getElementById("blood_pressure");
  const cholInput = document.getElementById("cholesterol");
  const bmiInput = document.getElementById("bmi");
  const actInput = document.getElementById("physical_activity");
  const stressInput = document.getElementById("stress_level");

  const ageVal = document.getElementById("age-val");
  const bpVal = document.getElementById("bp-val");
  const cholVal = document.getElementById("chol-val");
  const bmiVal = document.getElementById("bmi-val");
  const actVal = document.getElementById("act-val");
  const stressVal = document.getElementById("stress-val");

  const progressCircle = document.getElementById("progress-circle");
  const probPercent = document.getElementById("prob-percent");
  const riskBadge = document.getElementById("risk-badge");
  const diagnosisText = document.getElementById("diagnosis-text");
  const diagnosisExp = document.getElementById("diagnosis-explanation");
  const riskFactorsList = document.getElementById("risk-factors-list");
  const guidanceText = document.getElementById("guidance-text");
  const vectorDisplay = document.getElementById("encoded-vector-display");
  const statusIndicator = document.getElementById("status-indicator");
  const statusText = document.getElementById("status-text");

  // Gauge calculation (circumference = 2 * PI * 76 = ~477.52)
  const radius = progressCircle.r.baseVal.value;
  const circumference = 2 * Math.PI * radius;
  progressCircle.style.strokeDasharray = `${circumference} ${circumference}`;
  progressCircle.style.strokeDashoffset = circumference;

  function setGauge(percent) {
    const offset = circumference - (percent / 100) * circumference;
    progressCircle.style.strokeDashoffset = offset;
    probPercent.textContent = `${percent.toFixed(1)}%`;

    if (percent < 35) {
      progressCircle.style.stroke = "#10b981"; // green
    } else if (percent < 60) {
      progressCircle.style.stroke = "#f59e0b"; // amber
    } else {
      progressCircle.style.stroke = "#ef4444"; // red
    }
  }

  // Update slider badge displays
  function updateSliderLabels() {
    ageVal.textContent = `${ageInput.value} yrs`;
    bpVal.textContent = `${bpInput.value} mmHg`;
    cholVal.textContent = `${cholInput.value} mg/dL`;
    bmiVal.textContent = `${parseFloat(bmiInput.value).toFixed(1)} kg/m²`;
    actVal.textContent = `${actInput.value} days/wk`;
    stressVal.textContent = `${stressInput.value} / 9`;
  }

  [ageInput, bpInput, cholInput, bmiInput, actInput, stressInput].forEach(slider => {
    slider.addEventListener("input", () => {
      updateSliderLabels();
      runAssessment(); // Live reactive calculation
    });
  });

  // Toggle button handlers
  function setupToggle(groupId, hiddenInputId) {
    const group = document.getElementById(groupId);
    const hidden = document.getElementById(hiddenInputId);
    group.querySelectorAll(".toggle-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        group.querySelectorAll(".toggle-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        hidden.value = btn.dataset.val;
        runAssessment();
      });
    });
  }

  setupToggle("sex-group", "sex");
  setupToggle("smoker-group", "smoker");
  setupToggle("diabetes-group", "diabetes");
  setupToggle("family-group", "family_history");

  // Presets handler
  document.querySelectorAll(".preset-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const p = PRESETS[btn.dataset.preset];
      if (!p) return;

      ageInput.value = p.age;
      bpInput.value = p.blood_pressure;
      cholInput.value = p.cholesterol;
      bmiInput.value = p.bmi;
      actInput.value = p.physical_activity;
      stressInput.value = p.stress_level;

      setToggleValue("sex-group", "sex", p.sex);
      setToggleValue("smoker-group", "smoker", p.smoker);
      setToggleValue("diabetes-group", "diabetes", p.diabetes);
      setToggleValue("family-group", "family_history", p.family_history);

      updateSliderLabels();
      runAssessment();
    });
  });

  function setToggleValue(groupId, hiddenId, val) {
    const hidden = document.getElementById(hiddenId);
    hidden.value = val;
    const group = document.getElementById(groupId);
    group.querySelectorAll(".toggle-btn").forEach(b => {
      if (b.dataset.val === val) {
        b.classList.add("active");
      } else {
        b.classList.remove("active");
      }
    });
  }

  // Get current form data
  function getFormData() {
    return {
      age: parseFloat(ageInput.value),
      sex: document.getElementById("sex").value,
      blood_pressure: parseFloat(bpInput.value),
      cholesterol: parseFloat(cholInput.value),
      bmi: parseFloat(bmiInput.value),
      smoker: document.getElementById("smoker").value,
      diabetes: document.getElementById("diabetes").value,
      physical_activity: parseFloat(actInput.value),
      family_history: document.getElementById("family_history").value,
      stress_level: parseFloat(stressInput.value)
    };
  }

  // Client-Side Math Fallback (One-Hot Encoded Pipeline)
  function clientInference(data) {
    const numVals = [
      data.age, data.blood_pressure, data.cholesterol, data.bmi, data.physical_activity, data.stress_level
    ];
    const scaledNums = numVals.map((v, i) => (v - CLIENT_MODEL.means[i]) / CLIENT_MODEL.scales[i]);

    // One-Hot Encoding (drop='first'): Male=1, Smoker Yes=1, Diabetes Yes=1, Family History Yes=1
    const sexMale = data.sex === "Male" ? 1.0 : 0.0;
    const smokerYes = data.smoker === "Yes" ? 1.0 : 0.0;
    const diabetesYes = data.diabetes === "Yes" ? 1.0 : 0.0;
    const familyYes = data.family_history === "Yes" ? 1.0 : 0.0;

    const encodedVector = [...scaledNums, sexMale, smokerYes, diabetesYes, familyYes];

    let z = CLIENT_MODEL.intercept;
    for (let i = 0; i < encodedVector.length; i++) {
      z += CLIENT_MODEL.coefficients[i] * encodedVector[i];
    }
    const prob = 1.0 / (1.0 + Math.exp(-z));
    const percent = prob * 100;
    const pred = prob >= 0.50 ? 1 : 0;

    let tier = "Moderate Risk";
    let badgeClass = "moderate";
    if (percent < 35) {
      tier = "Low Risk";
      badgeClass = "low";
    } else if (percent > 60) {
      tier = "High Risk";
      badgeClass = "high";
    }

    const factors = [];
    if (smokerYes) factors.push({ text: "Active Tobacco Smoking (Statistically verified risk factor, p=0.048)", level: "red" });
    if (data.blood_pressure >= 130) factors.push({ text: `Elevated Systolic Blood Pressure (${data.blood_pressure} mmHg - Stage 1/2 Hypertension)`, level: "red" });
    if (data.cholesterol >= 200) factors.push({ text: `Hypercholesterolemia (${data.cholesterol} mg/dL - Above standard threshold)`, level: "amber" });
    if (data.bmi >= 30) factors.push({ text: `Obesity category BMI (${data.bmi.toFixed(1)} kg/m²)`, level: "amber" });
    else if (data.bmi >= 25) factors.push({ text: `Overweight BMI (${data.bmi.toFixed(1)} kg/m²)`, level: "amber" });
    if (diabetesYes) factors.push({ text: "Diagnosed Diabetes Mellitus comorbidity", level: "amber" });
    if (familyYes) factors.push({ text: "Familial predisposition / positive cardiovascular history", level: "amber" });
    if (data.physical_activity <= 1) factors.push({ text: "Sedentary lifestyle (Low weekly physical activity)", level: "amber" });
    if (data.stress_level >= 7) factors.push({ text: `Severe perceived psychological stress (${data.stress_level}/9)`, level: "amber" });
    if (factors.length === 0) factors.push({ text: "No acute adverse cardiovascular indicators detected", level: "green" });

    return {
      prediction: pred,
      diagnosis: pred === 1 ? "Positive (Heart Disease Indicated)" : "Negative (Low Likelihood of Disease)",
      probability_percent: percent,
      risk_tier: tier,
      badge_class: badgeClass,
      risk_factors: factors,
      encoded_vector: {
        "age (scaled)": scaledNums[0].toFixed(3),
        "blood_pressure (scaled)": scaledNums[1].toFixed(3),
        "cholesterol (scaled)": scaledNums[2].toFixed(3),
        "bmi (scaled)": scaledNums[3].toFixed(3),
        "physical_activity (scaled)": scaledNums[4].toFixed(3),
        "stress_level (scaled)": scaledNums[5].toFixed(3),
        "sex_Male (OHE)": sexMale,
        "smoker_Yes (OHE)": smokerYes,
        "diabetes_Yes (OHE)": diabetesYes,
        "family_history_Yes (OHE)": familyYes
      }
    };
  }

  // Render Result to UI
  function renderResult(res) {
    setGauge(res.probability_percent);

    riskBadge.textContent = res.risk_tier;
    riskBadge.className = `badge ${res.badge_class}`;

    diagnosisText.textContent = res.diagnosis;

    if (res.probability_percent < 35) {
      diagnosisExp.textContent = "The evaluated physiological vitals and lifestyle parameters show minimal indicators for cardiovascular risk.";
      guidanceText.textContent = "Maintain current balanced cardiovascular lifestyle. Continue regular routine health checkups and balanced nutrition.";
    } else if (res.probability_percent < 60) {
      diagnosisExp.textContent = "Clinical vitals suggest intermediate cardiac strain. Lifestyle intervention and continuous observation recommended.";
      guidanceText.textContent = "Schedule routine blood pressure and lipid monitoring. Implement dietary moderation (reduced sodium, lower saturated fats) and aerobic exercise.";
    } else {
      diagnosisExp.textContent = "Multiple clinical markers (e.g. smoking, hypertension, or elevated cholesterol) indicate elevated probability of heart disease.";
      guidanceText.textContent = "Clinical consultation with a cardiologist recommended. Smoking cessation, structured hypertension therapy, and lipid management are strongly advised.";
    }

    // Factors list
    riskFactorsList.innerHTML = "";
    res.risk_factors.forEach(f => {
      const li = document.createElement("li");
      li.innerHTML = `<span class="bullet ${f.level}"></span> ${f.text}`;
      riskFactorsList.appendChild(li);
    });

    // Encoded vector list
    vectorDisplay.innerHTML = "";
    for (const [k, v] of Object.entries(res.encoded_vector)) {
      const item = document.createElement("div");
      item.className = "vector-item";
      item.innerHTML = `<span>${k}</span><strong>${v}</strong>`;
      vectorDisplay.appendChild(item);
    }
  }

  // Core Assessment Runner (Dual API + Client Mode)
  async function runAssessment() {
    const data = getFormData();

    try {
      // Attempt API call to serverless backend
      const response = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        const apiRes = await response.json();
        statusIndicator.className = "status-indicator online";
        statusText.textContent = "API Active";
        // Format factors
        const formattedFactors = apiRes.contributing_risk_factors.map(t => ({
          text: t,
          level: t.includes("Smoking") || t.includes("Hypertension") ? "red" : "amber"
        }));
        if (formattedFactors.length === 0) {
          formattedFactors.push({ text: "No acute adverse cardiovascular indicators detected", level: "green" });
        }

        renderResult({
          prediction: apiRes.prediction,
          diagnosis: apiRes.diagnosis,
          probability_percent: apiRes.probability_percent,
          risk_tier: apiRes.risk_tier,
          badge_class: apiRes.badge_color === "red" ? "high" : apiRes.badge_color === "amber" ? "moderate" : "low",
          risk_factors: formattedFactors,
          encoded_vector: apiRes.encoded_feature_vector
        });
        return;
      }
    } catch (err) {
      // Fallback silently to client inference
    }

    // Client-side execution
    statusIndicator.className = "status-indicator client";
    statusText.textContent = "Client Engine";
    const clientRes = clientInference(data);
    renderResult(clientRes);
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    runAssessment();
  });

  // Initial calculation
  updateSliderLabels();
  runAssessment();
});
