export type GuideStep = {
  path: string;
  title: string;
  body: string;
};

export const MANAGER_GUIDE: GuideStep[] = [
  {
    path: "/",
    title: "Dashboard",
    body: "Your studio at a glance: who is signed in, team hours this week versus last week (every employee added together), project status, and unpaid invoices. Refresh pulls the latest figures. Nothing here is edited by staff.",
  },
  {
    path: "/live",
    title: "Live",
    body: "See each person in real time: signed in, on break, idle, or offline, plus the active window and latest screenshot. Open Day detail for the full punch timeline.",
  },
  {
    path: "/employees",
    title: "Employees",
    body: "Add staff, set login email and password, and copy the PC enroll code. Each computer must be enrolled once. You can edit a person’s details here later.",
  },
  {
    path: "/projects",
    title: "Projects",
    body: "Create jobs with client (staff see [Initial] · location only), scope, Detailer + Engineer. Staff move design phases freely; Advance pending badge if deposit unpaid. Hard lock only Stamped / Field / Run. Staff log end-of-day %; Admin audits history (40%→50%).",
  },
  {
    path: "/payments",
    title: "Payments",
    body: "Admin/Manager only. From a payment-gate message, use Go to Payments — the deposit invoice form opens for that project. Set status to Paid, then move the job on the Design Queue.",
  },
  {
    path: "/reports",
    title: "Reports",
    body: "Download attendance and hours as Excel, CSV, or PDF for a day or month. Dates use Pakistan time (PKT).",
  },
  {
    path: "/account",
    title: "Account & appearance",
    body: "Change your name, email, or password. Use Appearance to switch Dark or Light mode. The choice is saved on this browser.",
  },
];

export const MANAGER_DAY_GUIDE: GuideStep = {
  path: "/day",
  title: "Day detail",
  body: "One person’s punches, hours, and screenshots for a date (Pakistan time). Open this from Live. Staff cannot edit hours from the web.",
};

export const STAFF_GUIDE: GuideStep[] = [
  {
    path: "/day",
    title: "My Day",
    body: "Your punches, hours, and screenshots for the selected date. Use the date control to review another day. You cannot change hours from the web.",
  },
  {
    path: "/projects",
    title: "My Projects",
    body: "Jobs assigned to you as Detailer or Engineer. End of day: open the job → set My % today (saved for Admin audit). You see only [Initial] · location for clients — not full firm names.",
  },
  {
    path: "/account",
    title: "Account",
    body: "Update your password and, if shown, your display name. Appearance lets you choose Dark or Light mode for this browser.",
  },
];
