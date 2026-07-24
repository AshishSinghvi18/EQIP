import React from 'react';
import { useStoriesQuery } from '../api/hooks';
import Badge from '../components/common/Badge';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { StoryItem } from '../types';

function Stories() {
  const storiesQuery = useStoriesQuery();

  if (storiesQuery.isLoading) {
    return <LoadingSpinner label="Loading story readiness…" />;
  }

  const stories: StoryItem[] = storiesQuery.data?.data ?? [];

  return (
    <Card title="Stories readiness board" subtitle="Delivery signals enriched with module quality context.">
      <div className="overflow-hidden rounded-3xl border border-white/10">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-white/10 text-left text-sm">
            <thead className="bg-slate-950/40 text-slate-400">
              <tr>
                <th className="px-5 py-4 font-medium">Story</th>
                <th className="px-5 py-4 font-medium">Owner</th>
                <th className="px-5 py-4 font-medium">Module</th>
                <th className="px-5 py-4 font-medium">Status</th>
                <th className="px-5 py-4 font-medium">QA signal</th>
                <th className="px-5 py-4 font-medium">Due</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 bg-white/5">
              {stories.map((story) => (
                <tr key={story.id} className="text-slate-300">
                  <td className="px-5 py-4">
                    <p className="font-medium text-slate-100">{story.id}</p>
                    <p className="mt-1 text-xs text-slate-500">{story.title}</p>
                  </td>
                  <td className="px-5 py-4">{story.owner}</td>
                  <td className="px-5 py-4">{story.module}</td>
                  <td className="px-5 py-4">
                    <Badge tone={story.risk === 'High' ? 'danger' : story.risk === 'Medium' ? 'warning' : 'success'}>{story.status}</Badge>
                  </td>
                  <td className="px-5 py-4 text-slate-400">{story.qaSignal}</td>
                  <td className="px-5 py-4">{story.dueDate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Card>
  );
}

export default Stories;
