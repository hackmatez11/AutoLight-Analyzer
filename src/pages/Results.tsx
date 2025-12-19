import { useEffect, useState } from 'react';
import { supabase, Fixture, FixtureModel, Project } from '../lib/supabase';
import { ChevronDown, ChevronUp, Download, ArrowLeft } from 'lucide-react';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

interface ExtendedFixture extends Fixture {
  selected_model?: FixtureModel;
  recommendations?: FixtureModel[];
  showRecommendations?: boolean;
}

export default function Results({
  projectId,
  onNavigate,
}: {
  projectId?: string;
  onNavigate: (page: string) => void;
}) {
  const [project, setProject] = useState<Project | null>(null);
  const [fixtures, setFixtures] = useState<ExtendedFixture[]>([]);
  const [allModels, setAllModels] = useState<FixtureModel[]>([]);
  const [totalCost, setTotalCost] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (projectId) {
      loadProjectData();
    }
  }, [projectId]);

  const loadProjectData = async () => {
    try {
      const { data: projectData, error: projectError } = await supabase
        .from('projects')
        .select('*')
        .eq('id', projectId)
        .maybeSingle();

      if (projectError) throw projectError;
      setProject(projectData);

      const { data: fixturesData, error: fixturesError } = await supabase
        .from('fixtures')
        .select(`
          *,
          selected_model:fixture_models!fixtures_selected_model_id_fkey(*)
        `)
        .eq('project_id', projectId);

      if (fixturesError) throw fixturesError;

      const { data: modelsData, error: modelsError } = await supabase
        .from('fixture_models')
        .select('*');

      if (modelsError) throw modelsError;
      setAllModels(modelsData || []);

      const fixturesWithRecommendations = (fixturesData || []).map((fixture) => {
        const currentType = fixture.selected_model?.fixture_type;
        const recommendations = (modelsData || [])
          .filter(
            (model) =>
              model.fixture_type === currentType &&
              model.id !== fixture.selected_model_id
          )
          .slice(0, 3);

        return {
          ...fixture,
          recommendations,
          showRecommendations: false,
        };
      });

      setFixtures(fixturesWithRecommendations);
      calculateTotalCost(fixturesWithRecommendations);
    } catch (error) {
      console.error('Error loading project data:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateTotalCost = (fixturesList: ExtendedFixture[]) => {
    const total = fixturesList.reduce((sum, fixture) => {
      const price = fixture.selected_model?.unit_price || 0;
      return sum + price * fixture.quantity;
    }, 0);
    setTotalCost(total);
  };

  const handleModelChange = async (fixtureId: string, newModelId: string) => {
    try {
      const { error } = await supabase
        .from('fixtures')
        .update({ selected_model_id: newModelId })
        .eq('id', fixtureId);

      if (error) throw error;

      const newModel = allModels.find((m) => m.id === newModelId);
      const updatedFixtures = fixtures.map((fixture) =>
        fixture.id === fixtureId
          ? { ...fixture, selected_model_id: newModelId, selected_model: newModel }
          : fixture
      );

      setFixtures(updatedFixtures);
      calculateTotalCost(updatedFixtures);
    } catch (error) {
      console.error('Error updating fixture model:', error);
    }
  };

  const toggleRecommendations = (fixtureId: string) => {
    setFixtures(
      fixtures.map((fixture) =>
        fixture.id === fixtureId
          ? { ...fixture, showRecommendations: !fixture.showRecommendations }
          : fixture
      )
    );
  };

  const exportToPDF = () => {
    const doc = new jsPDF();

    doc.setFontSize(20);
    doc.text('Lighting Analysis Quotation', 14, 20);

    doc.setFontSize(11);
    doc.text(`Project: ${project?.name || 'N/A'}`, 14, 30);
    doc.text(`Date: ${new Date().toLocaleDateString()}`, 14, 36);
    doc.text(`Total Cost: $${totalCost.toFixed(2)}`, 14, 42);

    const tableData = fixtures.map((fixture) => [
      fixture.detected_symbol,
      fixture.room_name,
      fixture.selected_model?.model_name || 'N/A',
      fixture.selected_model?.manufacturer || 'N/A',
      fixture.quantity.toString(),
      `$${fixture.selected_model?.unit_price.toFixed(2) || '0.00'}`,
      `$${((fixture.selected_model?.unit_price || 0) * fixture.quantity).toFixed(2)}`,
    ]);

    autoTable(doc, {
      startY: 50,
      head: [['Symbol', 'Room', 'Model', 'Manufacturer', 'Qty', 'Unit Price', 'Total']],
      body: tableData,
      theme: 'grid',
      styles: { fontSize: 9 },
      headStyles: { fillColor: [59, 130, 246] },
    });

    const finalY = (doc as any).lastAutoTable.finalY || 50;
    doc.setFontSize(12);
    doc.text(`Total Project Cost: $${totalCost.toFixed(2)}`, 14, finalY + 10);

    doc.save(`${project?.name || 'quotation'}_${new Date().getTime()}.pdf`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 dark:text-gray-400 mb-4">Project not found</p>
        <button
          onClick={() => onNavigate('dashboard')}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => onNavigate('dashboard')}
            className="flex items-center text-blue-600 dark:text-blue-400 hover:underline mb-2"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Dashboard
          </button>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{project.name}</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Uploaded on {new Date(project.upload_date).toLocaleDateString()}
          </p>
        </div>
        <button
          onClick={exportToPDF}
          className="flex items-center space-x-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors"
        >
          <Download className="w-5 h-5" />
          <span>Download PDF</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-600 dark:text-gray-400">Total Fixtures</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{fixtures.length}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-600 dark:text-gray-400">Average Lux</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {project.average_lux.toFixed(0)}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-600 dark:text-gray-400">Total Cost</p>
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">
            ${totalCost.toFixed(2)}
          </p>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Detected Fixtures & Recommendations
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Symbol
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Room
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Selected Model
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Qty
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Unit Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Total Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {fixtures.map((fixture) => (
                <>
                  <tr key={fixture.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                      {fixture.detected_symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                      {fixture.room_name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {fixture.selected_model?.model_name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {fixture.selected_model?.manufacturer} - {fixture.selected_model?.wattage}W
                        </p>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                      {fixture.quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                      ${fixture.selected_model?.unit_price.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                      ${((fixture.selected_model?.unit_price || 0) * fixture.quantity).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {fixture.recommendations && fixture.recommendations.length > 0 && (
                        <button
                          onClick={() => toggleRecommendations(fixture.id)}
                          className="flex items-center text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          {fixture.showRecommendations ? (
                            <>
                              <ChevronUp className="w-4 h-4 mr-1" />
                              Hide
                            </>
                          ) : (
                            <>
                              <ChevronDown className="w-4 h-4 mr-1" />
                              Alternatives
                            </>
                          )}
                        </button>
                      )}
                    </td>
                  </tr>
                  {fixture.showRecommendations && fixture.recommendations && (
                    <tr>
                      <td colSpan={7} className="px-6 py-4 bg-blue-50 dark:bg-blue-900/20">
                        <div className="space-y-2">
                          <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                            Alternative Options:
                          </p>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {fixture.recommendations.map((rec) => (
                              <button
                                key={rec.id}
                                onClick={() => handleModelChange(fixture.id, rec.id)}
                                className="text-left p-4 bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-400 transition-colors"
                              >
                                <p className="font-medium text-gray-900 dark:text-white">
                                  {rec.model_name}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                  {rec.manufacturer} - {rec.wattage}W - {rec.lumens}lm
                                </p>
                                <p className="text-sm font-semibold text-blue-600 dark:text-blue-400 mt-2">
                                  ${rec.unit_price.toFixed(2)}
                                </p>
                                <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                                  {rec.description}
                                </p>
                              </button>
                            ))}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
            <tfoot className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <td
                  colSpan={5}
                  className="px-6 py-4 text-right text-sm font-semibold text-gray-900 dark:text-white"
                >
                  Total Project Cost:
                </td>
                <td
                  colSpan={2}
                  className="px-6 py-4 text-sm font-bold text-green-600 dark:text-green-400"
                >
                  ${totalCost.toFixed(2)}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  );
}
