import { Octokit } from "@octokit/rest";

export default async function handler(req, res) {
  // Only allow POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { slug, token } = req.body;

  // Simple token verification (you should use a more robust method in production)
  if (token !== process.env.DELETE_TOKEN) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  if (!slug) {
    return res.status(400).json({ error: 'Slug is required' });
  }

  try {
    const octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN
    });

    const owner = process.env.GITHUB_OWNER || 'propagatemedia';
    const repo = process.env.GITHUB_REPO || 'freshsites-outreach';
    const path = `docs/demos/${slug}.html`;

    // First, get the file to obtain its SHA (required for deletion)
    const { data: fileData } = await octokit.repos.getContent({
      owner,
      repo,
      path,
      ref: 'main'
    });

    // Delete the file
    await octokit.repos.deleteFile({
      owner,
      repo,
      path,
      message: `Remove demo for ${slug} via user request`,
      sha: fileData.sha,
      branch: 'main'
    });

    // Optionally, update the demo_url in the SQLite database to NULL
    // Since we don't have direct DB access here, we could call another API or rely on a separate cleanup.
    // For simplicity, we'll just note that the demo is removed.

    return res.status(200).json({ success: true, message: `Demo ${slug} deleted` });
  } catch (error) {
    console.error('Error deleting demo:', error);
    return res.status(500).json({ error: 'Failed to delete demo' });
  }
}