export const getLexaResponse = (message) => {
    const lowerMsg = message.toLowerCase();

    // Greetings
    if (lowerMsg.match(/\b(hi|hello|hey|greetings|start)\b/)) {
        return "Hello! I'm Lexa, your EscrowGig assistant. I can help you understand how our platform works, explain the escrow process, or guide you through disputes. What would you like to know?";
    }

    // Escrow / How it works
    if (lowerMsg.match(/\b(escrow|work|secure|safe)\b/)) {
        return "EscrowGig uses M-Pesa Escrow to ensure safety. Here's how it works:\n1. Client creates a project and deposits funds.\n2. Funds are held securely in our M-Pesa Escrow Vault.\n3. Freelancer does the work and submits it.\n4. Client approves, and funds are instantly released to the Freelancer's M-Pesa.";
    }

    // Money / Deposit / Payment
    if (lowerMsg.match(/\b(deposit|pay|money|mpesa|funds|cost|fee)\b/)) {
        return "All payments are handled via M-Pesa. Clients deposit funds into escrow to start a project. We charge a flat 5% platform fee on all transactions. Funds are only released when work is approved.";
    }

    // Disputes
    if (lowerMsg.match(/\b(dispute|conflict|fight|refund|issue|problem)\b/)) {
        return "If there's an issue, you can raise a 'Dispute' from the project dashboard. Our AI Analyzer will first review the case and suggest a fair resolution. If that fails, a human admin will review the evidence and make a final binding decision.";
    }

    // Hiring / Freelancing
    if (lowerMsg.match(/\b(hire|client|freelancer|job|gig)\b/)) {
        return "To hire, simply 'Post a Project' from your dashboard. To find work, browse the 'Find Work' section and apply to projects that match your skills. You'll be notified if a client accepts your proposal.";
    }

    // Profile
    if (lowerMsg.match(/\b(profile|edit|update|change)\b/)) {
        return "You can edit your profile by clicking on your name or avatar in the top right corner of the dashboard. You can update your skills, bio, professional details, and social links there.";
    }

    // Freelancer readiness / competency
    if (lowerMsg.match(/\b(competency|readiness|verification|verified|trust|score|proposal)\b/)) {
        return "Freelancer proposals are checked against the job requirements, and your profile has a readiness benchmark. Improve it by choosing the right profession, adding at least 3 relevant skills, writing a clear bio, adding verified GitHub/LinkedIn/portfolio links, and making each proposal specific to the client's project.";
    }

    // Fallback
    return "I'm not sure about that one yet. I'm trained to help with Escrow, Payments, Disputes, and Account basics. You can also contact our support team at support@escrowgig.co.ke for complex queries.";
};
